# coding=utf8
from lxml import etree
import pymongo
import redis
import time
import urllib2,urllib
import re
#aclii处理编码问题,'ascii' codec can't decode byte 0xe8 in position 0: ordinal not in range(128)
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
#ajax用json解析
import jsonpath
import json
# url : https://www.zhihu.com + redis里的url
class answer_page():
    def return_url(self):
        # 默认使用0号
        try:
            r = redis.StrictRedis(host='localhost', port=6379, db=0)
        except Exception, e:
            print e.message
        try:
            url_used = r.spop('urls_no_use')
            if not r.sismember('urls_used',url_used):
                print 'redis中还有{}个url'.format(r.scard('urls_no_use'))
                print '已经爬取了{}个url'.format(r.scard('url_used'))
                r.sadd('url_used',url_used)
                return url_used
        except:
            return 0

    def answer_response(self):
        question_url = self.return_url()
        while question_url != None:
            question_number = re.match(r'/question/(\d+)',question_url).group(1)
            url = 'https://www.zhihu.com{}'.format(question_url)
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
                'Cookie': 'q_c1=d1dc3d0924df403f881130e4f95f30ad|1520215343000|1520215343000; _zap=6c5ddb9e-e372-48aa-9a9a-53af9092ee81; _xsrf=0f40eb2c05cb329c8b490d62fa174c3b; d_c0="AOBsjE5rPQ2PTud-gcrXUq0w9bgl3wVhXD8=|1520240069"; __utmv=51854390.100--|2=registration_date=20160303=1^3=entry_date=20160303=1; aliyungf_tc=AQAAAM4fSHwRTgkAVbHseMrp8X+vGySv; capsion_ticket="2|1:0|10:1520269385|14:capsion_ticket|44:MGFiNDBjYThiMjM2NGJkNjk4NjRkZDY0ZmZlNDJhZjg=|3afeb1fbd55204a95facf8713913c63f03f71082bed5707e9919f729dcf14995"; z_c0="2|1:0|10:1520269398|4:z_c0|92:Mi4xRU5TMEFnQUFBQUFBNEd5TVRtczlEU1lBQUFCZ0FsVk5Wc2FLV3dDR3RJTkdSb3ZuZWxNeUN5TFZKa0V2MTdqUmRB|baa2dfcd6c9c949b372028b9d962a977374f36adee18c14c6727988b3546a0c2"; __utma=51854390.1689567540.1520240071.1520260789.1520270805.4; __utmb=51854390.0.10.1520270805; __utmc=51854390; __utmz=51854390.1520270805.4.4.utmcsr=zhihu.com|utmccn=(referral)|utmcmd=referral|utmcct=/',
                'Host': 'www.zhihu.com',
                'Referer': url,
                'X-UDID': 'AOBsjE5rPQ2PTud-gcrXUq0w9bgl3wVhXD8=',
                'authorization': 'Bearer 2|1:0|10:1520269398|4:z_c0|92:Mi4xRU5TMEFnQUFBQUFBNEd5TVRtczlEU1lBQUFCZ0FsVk5Wc2FLV3dDR3RJTkdSb3ZuZWxNeUN5TFZKa0V2MTdqUmRB|baa2dfcd6c9c949b372028b9d962a977374f36adee18c14c6727988b3546a0c2',
            }

            request = urllib2.Request(url,headers=headers) #data=data,
            response = urllib2.urlopen(request).read()
            selector = etree.HTML(response)
            title = selector.xpath('//h1[@class="QuestionHeader-title"]/text()')
            title = title[0]
            print title
            num = selector.xpath('//h4[@class="List-headerText"]//span/text()')
            num = num[0]
            num = int(num.replace(',',''))
            print num
            #处理ajax查找最高的点赞数
            # 若从全部回答中搜，则用以下条件
            # while offset+20 < num and max_num > offset:
            #     offset += 20
            # 由于回答的顺序跟点赞数有一定相关性，可取前60条大致满足结果却能省下无数的工作
            offset = 0
            max_num = num
            max_number = 0
            while offset < 60 and max_num > offset:
                limit = 5
                sort_by = 'default'
                data = {
                    'include': 'data[*].is_normal,admin_closed_comment,reward_info,is_collapsed,annotation_action,annotation_detail,collapse_reason,is_sticky,collapsed_by,suggest_edit,comment_count,can_comment,content,editable_content,voteup_count,reshipment_settings,comment_permission,created_time,updated_time,review_info,relevant_info,question,excerpt,relationship.is_authorized,is_author,voting,is_thanked,is_nothelp,upvoted_followees;data[*].mark_infos[*].url;data[*].author.follower_count,badge[?(type=best_answerer)].topics',
                    'offset': offset,
                    'limit': limit,
                    'sort_by': sort_by
                    }
                data = urllib.urlencode(data)
                ajax_url = 'https://www.zhihu.com/api/v4/questions/{}/answers'.format(question_number) + '?' + data  #.format(question_url)
                ajax_request = urllib2.Request(ajax_url,headers=headers)
                ajax_response = urllib2.urlopen(ajax_request)
                ajax_response = ajax_response.read()
                # 把json格式字符串转换成python对象
                jsonobj = json.loads(ajax_response)
                agree_nums = jsonpath.jsonpath(jsonobj, '$.data..voteup_count')

                for agree in agree_nums:
                    if agree > max_number:
                        #取到了更大的点赞数，更新mongodb的数据
                        max_number = agree
                        max_index = agree_nums.index(max_number)
                        answer = jsonpath.jsonpath(jsonobj,'$.data[{}].content'.format(max_index))
                        answer = answer[0]
                        answer = re.sub(r'<.*?>','', answer)
                offset +=5

            answer = '该回答有{}个赞.{}'.format(max_number,answer)
            print '解析数据完成，准备存储到mongodb'
            client = pymongo.MongoClient("localhost", 27017)
            db = client.test
            topic_answer = db.topic_answer
            print '正在将一条数据写入mongodb'
            s1 = {'title': title, 'answer':answer}
            topic_answer.insert(s1)
            print '写入mongodb完成'
            question_url = self.return_url()
            time.sleep(0.5)
        return 0