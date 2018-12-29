
# coding: utf-8

# In[1]:


from PIL import Image
import subprocess
import re
import os
import time
import io


# In[2]:


def capture_img():
    subprocess.call('.\\adb\\adb shell /system/bin/screencap -p /sdcard/screenshot.png')
    time.sleep(0.1)
    subprocess.call('.\\adb\\adb pull /sdcard/screenshot.png %s' % './tmp/screenshot.png')
    time.sleep(0.1)

    im = Image.open('./tmp/screenshot.png')
    im = im.convert('RGB').crop((0,300,1080,600))
#     im.thumbnail((150,720))
    im.save('./tmp/screenshot.jpg')

    with open('./tmp/screenshot.jpg', 'rb') as fp:
        return fp.read()


# In[3]:


from aip_key import APP_ID
from aip_key import API_KEY
from aip_key import SECRET_KEY

# In[4]:


from aip import AipOcr

client = AipOcr(APP_ID, API_KEY, SECRET_KEY)


# In[5]:


def search_ans():
    image = capture_img()

    print('Parsing pic...')
    rst = client.basicGeneral(image)

    question = ''.join([p['words'] for p in rst['words_result']])

    if question != None and question != '':
#         question = question.split('.')[1]

        qs = re.split(r"\.|,|。|，",question)
        if len(qs) > 1:
            question = ''.join(qs[1:])
        print('question:', question)
                
        os.system('start www.baidu.com/s?wd=%s' % question)
        # os.system('start www.google.com/search?q=%s' % question)

    else:
        print('No question found!')


# In[ ]:


while True:
    ipt = input()
    if ipt == 'q':
        break
    else:
        search_ans()

