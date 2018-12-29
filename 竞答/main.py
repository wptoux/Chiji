import time
import random

import lmdb
import cv2
import numpy as np
import editdistance

import utils


def _match(img, tp):
    match = cv2.matchTemplate(img, tp, cv2.TM_CCOEFF_NORMED)
    p = np.unravel_index(match.argmax(), match.shape)
    return match.max(), (p[0], p[0] + tp.shape[0], p[1], p[1] + tp.shape[1])


class State:
    def __init__(self):
        self.state = 'startup'

    def chg_state(self, state_to):
        print('Current state:', self.state)
        print('Change to:', state_to)

        self.state = state_to


if __name__ == '__main__':
    env = lmdb.open('db')

    content_offset = 900
    regions = [(0, 280, 0, 1080), (300, 450, 120, 980), (450, 650, 120, 980), (650, 800, 120, 980), (800, 1000, 120, 980)]

    tp_startup = cv2.imread('./template/startup.png')
    tp_continue = cv2.imread('./template/continue.png')
    tp_right = cv2.imread('./template/right.png')
    tp_retry = cv2.imread('./template/retry.png')
    tp_main = cv2.imread('./template/main.png')

    state = State()
    ocr_rst = []

    while True:
        img = utils.capture_img()

        score, pos = _match(img, tp_continue)
        if score > 0.9:  # game end
            utils.tap((pos[0] + pos[1]) / 2, (pos[2] + pos[3]) / 2)
            state.chg_state('retry')
            time.sleep(0.3)

        elif state.state == 'startup':
            score, pos = _match(img, tp_startup)

            if score > 0.9:
                utils.tap((pos[0] + pos[1]) / 2, (pos[2] + pos[3]) / 2)
                state.chg_state('run')
                time.sleep(1)
            else:
                time.sleep(0.3)

        elif state.state == 'run':
            score, pos = _match(img, tp_main)
            if score > 0.20:
                simg = img[content_offset:, :, :]
                print('Call ocr...')
                ocr_rst = utils.ocr(simg, regions)
                print('Question:', ocr_rst)

                if '' not in ocr_rst:
                    question, opt1, opt2, opt3, opt4 = ocr_rst

                    with env.begin() as txn:
                        ans = txn.get(question.encode())

                    if ans is None:
                        select = random.randrange(1, 5)
                    else:
                        ans = ans.decode()
                        print('Memory hit!', ans)
                        d1 = editdistance.eval(ans, opt1)
                        d2 = editdistance.eval(ans, opt2)
                        d3 = editdistance.eval(ans, opt3)
                        d4 = editdistance.eval(ans, opt4)

                        select = np.argmin([d1, d2, d3, d4]) + 1

                    print('Choose:', select)

                    r = regions[select]
                    utils.tap((r[0] + r[1]) / 2 + content_offset, (r[2] + r[3]) / 2)
                    time.sleep(0.2)
                    state.chg_state('parse_rst')
        elif state.state == 'parse_rst':
            simg = img[content_offset:, :, :]
            score, pos = _match(simg[300:, :, :], tp_right)
            pos = (pos[0] + 300, pos)

            if score > 0.6:
                # print('Call ocr...')
                # ocr_rst = utils.ocr(simg, regions)
                print('Question:', ocr_rst)
                if '' not in ocr_rst:
                    question = ocr_rst[0]

                    for i, r in enumerate(regions[1:]):
                        if r[0] < pos[0] < r[1]:
                            ans = ocr_rst[i + 1]
                            print('Put in memory: Q:', question, 'A:', ans)

                            with env.begin(write=True) as txn:
                                txn.put(question.encode(), ans.encode())

                            state.chg_state('run')
                            time.sleep(4)
                            break
        elif state.state == 'retry':
            score, pos = _match(img, tp_retry)

            if score > 0.9:
                utils.tap((pos[0] + pos[1]) / 2, (pos[2] + pos[3]) / 2)
                time.sleep(0.5)
                state.chg_state('run')












