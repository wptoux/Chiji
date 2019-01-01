import concurrent.futures
import subprocess
import time
import re

import numpy as np

import cv2
from aip import AipOcr

# import pytesseract

import key

client = AipOcr(key.AIP_APP_ID, key.AIP_API_KEY, key.AIP_SECRET_KEY)

executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)


def capture_img():
    print('Capturing img...', end=' ')
    st = time.time()
    pipe = subprocess.Popen(".\\adb\\adb shell screencap -p",
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, shell=True)
    image_bytes = pipe.stdout.read().replace(b'\r\n', b'\n')
    image = cv2.imdecode(np.fromstring(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    print('Time:', time.time() - st)
    return image


def tap(x, y):
    subprocess.call('.\\adb\\adb shell input tap %d %d' % (y, x))


def get_text_in_region(aip_rst, region):
    s = ''
    if 'words_result' in aip_rst:
        words = []
        for p in aip_rst['words_result']:
            loc = p['location']
            if loc['top'] > region[0] and loc['top'] + loc['height'] < region[1] \
                    and loc['left'] > region[2] and loc['left'] + loc['width'] < region[3]:
                if loc['left'] < 1080 / 2:  # only get words that starts from left
                    words.append(p['words'])
        s = ''.join(words)

    # if s != '':
    #     # remove heading, like 1. A. B.
    #     if re.match(r"^A|B|C|\d+\.|,|。|，", s) is not None:
    #         ss = re.split(r"[.,。，]", s)
    #         if len(ss) > 1:
    #             s = ''.join(ss[1:])

    return s


def ocr(im, regions, engine='baidu_single'):
    if engine == 'baidu':
        _, byte_arr = cv2.imencode('.jpg', im, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        aip_rst = client.general(byte_arr.tobytes())
        return [get_text_in_region(aip_rst, region) for region in regions]
    elif engine == 'baidu_single':
        ocr_im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

        ret = []
        tasks = []
        for r in regions:
            _im = ocr_im[r[0]:r[1], r[2]:r[3]]

            _im = cv2.resize(_im, (int(_im.shape[1] / 2.5), int(_im.shape[0] // 2.5)))

            _, byte_arr = cv2.imencode('.jpg', _im, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            # aip_rst = client.basicGeneral(byte_arr.tobytes(), {'probability': 'true'})
            tasks.append(executor.submit(lambda x: client.basicGeneral(x.tobytes(), {'probability': 'true'}), byte_arr))

        for t in tasks:
            aip_rst = t.result()
            words = []
            for p in aip_rst['words_result']:
                words.append(p['words'])
            s = ''.join(words)
            ret.append(s)
        return ret

    elif engine == 'tesseract':
        ret = []
        for r in regions:
            ocr_im = im[r[0]:r[1], r[2]:r[3], :]
            # ocr_im = cv2.resize(ocr_im, (100, int(ocr_im.shape[1] / ocr_im.shape[0] * 100)))
            ocr_im = cv2.adaptiveThreshold(cv2.cvtColor(ocr_im, cv2.COLOR_BGR2GRAY),
                                           255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            txt = pytesseract.image_to_string(ocr_im, lang='chi_sim', config='--oem 1')
            txt = re.sub(r'\s+', '', txt)
            ret.append(txt)

        return ret
    else:
        raise Exception()
