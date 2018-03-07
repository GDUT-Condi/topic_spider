# coding=utf8
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
# WebDriverWait 库，负责循环等待
from selenium.webdriver.support.ui import WebDriverWait
# expected_conditions 类，负责条件出发
from selenium.webdriver.support import expected_conditions as EC
#配置部分
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from lxml import etree
import redis
import pymongo
import json
import sys

class zhihu_login():
    def __init__(self):
        self.dcap = dict(DesiredCapabilities.PHANTOMJS)
        # 不载入图片，爬页面速度会快很多
        self.dcap["phantomjs.page.settings.loadImages"] = False
        # 设置代理
        self.service_args = ['--proxy=127.0.0.1:9999', '--proxy-type=socks5']
        # 从USER_AGENTS列表中随机选一个浏览器头，伪装浏览器
        self.dcap["phantomjs.page.settings.userAgent"] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
        # headers = {
        #     'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
        #     'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/603.2.4 (KHTML, like Gecko) Version/10.1.1 Safari/603.2.4',
        #     'Connection': 'keep-alive'
        # }
        self.topic_dict = {'互联网': 99, '法律': 215, '游戏': 253, '生活': 307, 'python爬虫': 181627}

    def login(self):
        driver = webdriver.PhantomJS(executable_path="../../Selenium_PhantomJS/phantomjs/bin/phantomjs",
                                     desired_capabilities = self.dcap) #使用代理加参数,service_args=self.service_args
        driver.set_window_size('600', '800')

        '''#前面部分代码用于填写登录信息并登录
        driver.get('https://www.zhihu.com/signin')
        time.sleep(2)
        driver.find_element_by_xpath('//input[@type="text"][@name="username"]').send_keys('18813290955')
        driver.find_element_by_xpath('//input[@type="password"]').send_keys('kang199544')
        driver.save_screenshot("login.png")
        driver.find_element_by_xpath('//button[@class="Button SignFlow-submitButton Button--primary Button--blue"]').click()
        time.sleep(2)
        driver.save_screenshot("login1.png")
        # 获取cookie并通过json模块将dict转化成str
        dictCookies = driver.get_cookies()
        jsonCookies = json.dumps(dictCookies)
        # 登录完成后，将cookie保存到本地文件
        with open('cookies.json', 'w') as f:
            f.write(jsonCookies)
        '''
        #利用cookies登录
        driver.get("http://www.zhihu.com/")
        driver.delete_all_cookies()
        with open('cookies.json', 'r') as f:
            listCookies = json.loads(f.read())
        for cookie in listCookies:
            driver.add_cookie({
                'domain': '.zhihu.com',  # 此处xxx.com前，需要带点
                'name': cookie['name'],
                'value': cookie['value'],
                'path': '/',
                "httponly": 'false',
                "secure": 'false'
            })
        # 再次访问页面，便可实现免登陆访问
        driver.get("http://www.zhihu.com/")
        time.sleep(1)
        try:
            # 页面一直循环，直到 "//a[@data-reactid='16']" 出现
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[@data-reactid='16']"))
            )
        except:
            print '出错了'
            driver.quit()
            return 0
        try:
            driver.find_element_by_xpath('//a[@data-reactid="16"]').click()

            try:
                element = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//a[@class ="js-send-digits digits-button"]'))
                )
                driver.find_element_by_xpath('//a[@class ="js-send-digits digits-button"]').click()
                captch = raw_input('输入手机获取的验证码')
                driver.find_element_by_xpath('//input[@class ="text digits"]').send_keys(captch)
                driver.find_element_by_xpath('//button[@class="submit zg-btn-blue"]').click()
                time.sleep(1)
            except:
                print '不用安全验证'

            self.topic = raw_input('请输入要爬取的话题')

            try:
                topic_id = self.topic_dict[self.topic]
                driver.find_element_by_xpath(
                    '//li[@class="zm-topic-cat-item"][@data-id={}]/a[@href]'.format(topic_id)).click()
                time.sleep(1)
            except:
                print '话题页面出错'
                driver.quit()
                return 0

            topic_num = 0
            # 默认使用0号
            r = redis.StrictRedis(host='localhost', port=6379, db=0)

            client = pymongo.MongoClient("localhost", 27017)
            db = client.test
            topic = db.topic

            page = raw_input('请输入要爬多少页')

            for i in range(int(page)):
                try:
                    start = time.time()
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//a[@class ="zg-btn-white zu-button-more"]'))
                    )
                    driver.find_element_by_xpath('//a[@aria-role="button"]').click()
                    time.sleep(2)
                    page_data = driver.page_source
                    print sys.getsizeof(page_data)
                    selector = etree.HTML(page_data)
                    topic_links_test  = selector.xpath('//div[@class="feed-item feed-item-hook  folding"]//a[@class="question_link"]/@href')
                    print len(topic_links_test)
                    topic_links = selector.xpath('//div[@class="zh-general-list clearfix"]/div[position()>{}]//a[@class="question_link"]/@href'.format(topic_num))
                    time.sleep(1)

                    # driver.save_screenshot("zhihu{}.png".format(i+1))
                    topics_name = selector.xpath(
                        '//div[@class="zh-general-list clearfix"]/div[position()>{}]//div[@class="feed-main"]//a[@class="question_link"]/text()'.format(
                            topic_num))
                    topics_author = selector.xpath(
                        '//div[@class="zh-general-list clearfix"]/div[position()>{}]//div[@class="feed-main"]//div[@class="zm-item-rich-text expandable js-collapse-body"]/@data-author-name'.format(
                            topic_num))
                    print '正在将话题数据写入mongodb'
                    for name, title in zip(topics_author, topics_name):
                        s1 = {'name': name, 'title': title.strip()}
                        topic.insert(s1)
                    print '话题数据写入mongodb完成'
                    print 'redis正在存储urls'
                    for topic_link in topic_links:
                            r.sadd('urls_no_use', topic_link)
                    print '第{}页写入完成'.format(i+1)
                    topic_num += len(topic_links)
                    end = time.time()
                    print end - start

                except:
                    print '加载失败'
                    driver.save_screenshot("topic0.png")
                    driver.quit()
                    return 0
        except:
            print '爬虫失败'
            driver.quit()
            return 0
        driver.quit()
        return 0