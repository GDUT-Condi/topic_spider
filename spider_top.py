# coding=utf8
from threading import Thread,Lock
import redis
from topic_zhihu import zhihu_login
from answer_parse import answer_page
from multiprocessing import	Process,Queue
import time,random

def parse_title():
    global r
    while True:
        mutexFlag = mutex.acquire(True)
        if mutexFlag:
            if r.scard('urls_no_use'):
                print '正在取知乎对应的最高点赞回答'
                mutex.release()
                answer_page().answer_response()
                time.sleep(random.random())
            else:
                mutex.release()
                print 'redis里的url已经爬取完成'
                break

def two_threading():
    try:
        parse1 = Thread(target=parse_title)
        parse2 = Thread(target=parse_title)
        parse1.start()
        parse2.start()
        parse1.join()
        parse2.join()
    except Exception, e:
        print '爬虫结束'

if __name__ == '__main__':
    #创建两个进程，一个存url,一个解析url的数据
    #	父进程创建Queue,并传给各个子进程:
    start = time.time()
    q = Queue()
    #创建一个互斥锁,默认未上锁
    # raw_input('按任意键开始')
    #两个线程对answer进行解析
    mutex = Lock()
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    pw = Process(target=zhihu_login().login())
    pr = Process(target=two_threading)
    pw.start()
    pr.start()
    pw.join()
    pr.join()
    end = time.time()
    print end-start
