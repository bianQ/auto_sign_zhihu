"""
Author  : Alan
Date    : 2019/2/21 15:15
Email   : vagaab@foxmail.com
"""

from sklearn import mixture
from keras.models import load_model
import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import requests

import base64
from io import BytesIO
import os
from threading import Thread
import time
import random

import Config


def recognize(model, im):
    im = centerExtend(im, radius=20)

    vec = np.asarray(im.convert('L')).copy()
    Y = []
    for i in range(vec.shape[0]):
        for j in range(vec.shape[1]):
            if vec[i][j] <= 200:
                Y.append([i, j])

    gmm = mixture.GaussianMixture(n_components=7, covariance_type='tied', reg_covar=1e2, tol=1e3, n_init=9)
    gmm.fit(Y)

    centers = gmm.means_
    centers.sort(axis=0)

    points = []
    for i in range(7):
        p_x = centers[i][0]
        p_y = centers[i][1]

        cr = crop(im, p_x, p_y, radius=20)
        cr = cr.resize((40, 40), Image.ANTIALIAS)

        X = np.asarray(cr.convert('L')).astype('float64')
        X[X <= 150] = -1
        X[X > 150] = 1
#                 x0 = np.expand_dims(X, axis=0)
        x1 = np.expand_dims([X], axis=3)

        if model.predict(x1)[0][0] < 0.5:
            points.append(i)

    return points


def centerExtend(im, width=400, height=88, radius=20):
    x1 = np.full((height+radius+radius, width+radius+radius), 255, dtype='uint8')
    x2 = np.asarray(im.convert('L'))
    x1[radius:radius+height,radius:radius+width] = x2
    return Image.fromarray(x1, 'L')


def crop(im, y, x, radius = 20):
    return im.crop((x-radius, y-radius, x+radius, y+radius))


def create_chrome():
    os.system('chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\selenum\AutomationProfile"')


def sleep():
    time.sleep(2 + random.randrange(-100, 100) / 100)

flag = False
t = Thread(target=create_chrome, daemon=True)
t.start()
chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=chrome_options, executable_path=r'C:\Program Files (x86)\Google\Chrome\Application\chromedriver')
driver.get('https://www.zhihu.com/signup?next=%2F')
try:
    driver.find_element_by_xpath("//div[@class='SignContainer-switch']/span").click()
except:
    flag = True
sleep()
while not flag:
    driver.find_element_by_name('username').send_keys(Config.username)
    driver.find_element_by_name('password').send_keys(Config.passwd)
    driver.find_element_by_xpath("//button[@class='Button SignFlow-submitButton Button--primary Button--blue']").click()
    try:
        captcha = driver.find_element_by_xpath("//div[@class='Captcha-englishContainer']/img")
    except:
        print('目前只支持识别中文验证码')
        driver.refresh()
        sleep()
        continue
    captcha = driver.find_element_by_xpath("//div[@class='Captcha-chineseContainer']/img")
    cap_im = captcha.get_attribute('src').replace('data:image/jpg;base64,', '').replace('%0A', '')
    im = Image.open(BytesIO(base64.b64decode(cap_im)))
    model = load_model('zheyeV3.keras')
    center = recognize(model, im)

    action = ActionChains(driver)
    for i in center:
        fx = random.randrange(-300, 300) / 100
        fy = random.randrange(-300, 300) / 100
        action.move_to_element_with_offset(captcha, 20 + i * 25 + fx, 25 + fy).click()
    action.perform()
    driver.find_element_by_xpath("//button[@class='Button SignFlow-submitButton Button--primary Button--blue']").click()
    flag = True
    print('验证码识别成功')

sleep()
cookies = driver.get_cookies()
cookies = {i['name']: i['value'] for i in cookies}
s = requests.session()
s.cookies.update(cookies)
header = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'
}
r = s.get('https://www.zhihu.com/api/v4/me', headers=header)
print(r.json()['name'])
driver.quit()
