# coding=utf-8
__author__ = 'Jerry'

import sys

reload(sys)
sys.setdefaultencoding('utf-8')
import hashlib
import re
import requests
import logging
import json
import datetime
import os

DEBUG_LEVEL = logging.DEBUG

root = logging.getLogger()
root.setLevel(DEBUG_LEVEL)
root.addHandler(logging.StreamHandler())

'''base exception class.
'''


class WechatPublicError(Exception):
    pass

'''raise when cookies expired.
'''


class WechatNeedLoginError(WechatPublicError):
    pass


'''rasie when unenable to login.
'''


class WechatLoginError(WechatPublicError):
    pass


class WechatPublic(object):
    def __init__(self, account, pwd, token=None, cookies=None, ifencodepwd=False, cgi_data=None):
        self.account = account
        if ifencodepwd:
            self.pwd = pwd
        else:
            self.pwd = hashlib.md5(pwd).hexdigest()
        self.wx_cookies = cookies
        self.latest_msg_id = 0
        self.token = token

        if self.token is None or self.wx_cookies is None:
            self.token = ''
            self.wx_cookies = ''
            self.login()
        self.cgi_data = cgi_data

    '''login to wechat, get token and cookies.

    Raise:
        WechatLoginError, when can not get token from respond.
    '''

    def login(self):
        url = 'https://mp.weixin.qq.com/cgi-bin/login?lang=zh_CN'
        payload = {
            'username': self.account,
            'imgcode': '',
            'f': 'json',
            'pwd': self.pwd,
        }
        headers = {
            'x-requested-with': 'XMLHttpRequest',
            'referer': 'https://mp.weixin.qq.com/cgi-bin/loginpage?t=wxm2-login&lang=zh_CN',
        }

        r = requests.post(url, data=payload, headers=headers, verify='cacert.pem')

        logging.info('------login------')
        logging.debug("respond:\t%s" % r.text)

        s = re.search(r'token=(\d+)', r.text)
        if not s:
            logging.error('Login Error!!!')
            raise Exception("Login error.")
        self.token = int(s.group(1))
        logging.debug('token:\t%d' % self.token)

        self.wx_cookies = ''
        for cookie in r.cookies:
            self.wx_cookies += cookie.name + '=' + cookie.value + ';'
        logging.debug('cookies:\t%s' % self.wx_cookies)
        logging.info('------end login------')

    def get_today_msg_list(self, frommsgid=0, offset=0):
        return self.get_msg_list(frommsgid=frommsgid, offset=offset, day=0)

    def get_yesterday_msg_list(self, frommsgid=0, offset=0):
        return self.get_msg_list(frommsgid=frommsgid, offset=offset, day=1)

    def get_cgi_data(self, frommsgid=0, offset=0, day=0):
        url = 'https://mp.weixin.qq.com/cgi-bin/message?t=message/list&frommsgid=%s&offset=%d&token=%s&count=20&day=%d&filterivrmsg=1' \
              % (frommsgid, offset, self.token, day)
        payload = {
            't': 'message/list',
            'frommsgid': frommsgid,
            'offset': offset,
            'token': self.token,
            'count': 20,
            'day': day,
            'filterivrmsg': 1
        }
        headers = {
            'x-requested-with': 'XMLHttpRequest',
            'referer': 'https://mp.weixin.qq.com/cgi-bin/loginpage?t=wxm2-login&lang=zh_CN',
            'cookie': self.wx_cookies,
        }

        r = requests.get(url, data=payload, headers=headers, verify='cacert.pem')

        c = "".join(r.text.split())
        all_str = re.search(r'cgiData={(.*)}seajs', c)
        if all_str is None:
            logging.error('get cgi data error.')
        else:
            self.cgi_data = all_str.group(1)

    '''get message list.

    raise:
        WechatNeedLoginError, when need re-login.

    returns:
        messages in dict.
    '''

    def get_msg_list(self, frommsgid=0, offset=0, day=0):
        # logging.info('------get_msg_list------')
        # /message?t=message/list&frommsgid=209607169&offset=20&count=20&day=0&filterivrmsg=1&token=2138261750
        url = 'https://mp.weixin.qq.com/cgi-bin/message?t=message/list&frommsgid=%s&offset=%d&token=%s&count=20&day=%d&filterivrmsg=1' \
              % (frommsgid, offset, self.token, day)
        payload = {
            't': 'message/list',
            'frommsgid': frommsgid,
            'offset': offset,
            'token': self.token,
            'count': 20,
            'day': day,
            'filterivrmsg': 1
        }
        headers = {
            'x-requested-with': 'XMLHttpRequest',
            'referer': 'https://mp.weixin.qq.com/cgi-bin/loginpage?t=wxm2-login&lang=zh_CN',
            'cookie': self.wx_cookies,
        }

        r = requests.get(url, data=payload, headers=headers, verify='cacert.pem')

        c = "".join(r.text.split())
        all_str = re.search(r'cgiData={(.*)}seajs', c)
        if all_str is None:
            logging.error('get cgi data error.')
        else:
            self.cgi_data = all_str.group(1)
        s = re.search(r'list:\((.*)\).msg_item', self.cgi_data)
        if s is None:
            logging.error('Sorry has no messages yet.')
        else:
            msg_list = s.group(1)
        # logging.debug('msg_list:\t%s' % msg_list)
        # logging.info('------end get_msg_list------')
        return msg_list

    '''get latest_msg_id.

    raise:
        None.

    returns:
        latest_msg_id.
    '''

    def get_latest_msg_id(self):
        latest_msg = re.search(r"latest_msg_id:'(\d+)'", self.cgi_data)
        lid = 0
        if latest_msg is None:
            logging.error('this day has no messages yet.')
        else:
            lid = latest_msg.group(1)
        return lid

    '''get total_count.

    raise:
        None.

    returns:
        total_count.
    '''

    def get_total_count(self):
        total_count = re.search(r"total_count:(\d+)", self.cgi_data)
        num = 0
        if total_count is None:
            logging.error('today has no messages yet.')
        else:
            num = total_count.group(1)
        return num

    ''' get message image.

    Args:
        msgid.
        dir, local dir to store this img.
    '''

    def get_msg_image(self, msgid=208579870, dir='', image_name=''):
        logging.info('------get_msg_image------')
        url = "https://mp.weixin.qq.com/cgi-bin/getimgdata"
        payload = {
            'token': self.token,
            'msgid': msgid,
            'mode': 'large',
        }
        headers = {
            'Cookie': self.wx_cookies,
        }

        r = requests.get(url, params=payload, headers=headers, verify='cacert.pem')
        respond_headers = r.headers
        if 'content-type' in respond_headers.keys() and not respond_headers['content-type'] == 'image/jpg':
            logging.error('download message image error, need re-login.')
            raise WechatNeedLoginError('download message image error, need re-login.')

        if dir == '':
            with open('%s.jpg' % image_name, 'wb+') as f:
                f.write(r.content)
                f.close()
        else:
            createdir(dir)
            with open('%s/%s.jpg' % (dir, image_name), 'wb+') as f:
                f.write(r.content)
                f.close()

        logging.info('------end get_msg_image------')


def createdir(path):
    path = path.strip()
    path = path.rstrip("\\")

    is_exist = os.path.exists(path)

    if not is_exist:
        os.makedirs(path)


def get_max_id(filename='lastid.txt'):
    max_id = 0
    if os.path.exists(filename):
        try:
            f = open(filename, 'r')
        except IOError:
            print "file open error"
        else:
            max_id = f.read()
            f.close()
            if max_id == '':
                max_id = 0
    return max_id


def set_max_id(filename='lastid.txt', max_id=0):
    f = open(filename, 'w')
    f.write(str(max_id))
    f.close()


def waitapp():
    import time
    for i in range(10, 0, -1):
        os.write(1, "\rThe application will be close in %d seconds..." % i)
        sys.stdout.flush()
        time.sleep(1)


def get_total_page(total_num=1, count=20):
    if total_num % count == 0:
        t_page = total_num / count
    else:
        t_page = total_num / count + 1
    return t_page


def get_day():
    day = 0
    while True:
        try:
            day = int(raw_input("please input the num.\n0---today\t1---yesterday\t2---the day before yesterday\n"))
        except BaseException:
            print "Please entry a number !"
            continue
        if day in [0, 1, 2]:
            break
        else:
            continue
    return day


def get_datetime(day):
    today = datetime.date.today()
    if day == 0:
        return today
    elif day == 1:
        oneday = datetime.timedelta(days=1)
        return today - oneday
    elif day == 2:
        twoday = datetime.timedelta(days=2)
        return today - twoday


def format_time(str):
    import time
    return int(time.mktime(time.strptime(str, '%Y-%m-%d %H:%M')))


def get_time():
    t = {}
    while True:
        try:
            begin_str = raw_input("please input the begin time.\neg:2015-08-15 18:00\t")
            end_str = raw_input("please input the end time.\neg:2015-08-16 18:00\t")
            begin_time = format_time(begin_str)
            end_time = format_time(end_str)
        except BaseException:
            print 'Please entry right begin_time and end_time!'
            continue
        if 0 < (end_time - begin_time) <= 86400 * 3:
            t['begin_time'] = begin_time
            t['end_time'] = end_time
            break
        else:
            print 'Wrong input!\nWe cam only get the latest three days picture messages!'
            continue
    return t


def get_filename(day):
    if day == 0:
        return 'today.txt'
    elif day == 1:
        return 'yesterday.txt'
    else:
        return 'maxid.txt'


if __name__ == '__main__':
    day = 7  # 7 means get lastest five days, but only the lastest three days image messages be stored on Tencent server
    t = get_time();
    mpwx = WechatPublic("your_username", "your_password")
    mpwx.get_cgi_data(day=day)
    latest_id = mpwx.get_latest_msg_id()
    total_num = mpwx.get_total_count()
    total_page = get_total_page(int(total_num))
    filename = get_filename(day)
    max_id = int(get_max_id(filename=filename))
    for i in range(0, total_page):
        all_str = mpwx.get_msg_list(frommsgid=latest_id, offset=i * 20, day=day)
        all_msg = json.loads(s=all_str, encoding='utf-8')

        msg_list = all_msg['msg_item']

        for msg in msg_list:
            if msg['type'] == 2 and int(msg['id']) > max_id and (
                    t['begin_time'] <= int(msg['date_time']) <= t['end_time']):
                if 'remark_name' in msg.keys():
                    uname = msg['remark_name'].decode('utf-8')
                else:
                    uname = msg['nick_name'].decode('utf-8')
                date_time = datetime.datetime.fromtimestamp(msg['date_time'])
                datedir = date_time.strftime('%Y-%m-%d')
                path = datedir + '/' + uname
                image_time = date_time.strftime('%H-%M')
                mpwx.get_msg_image(msgid=msg['id'], dir=path,
                                   image_name=uname + '_' + image_time + '_' + str(msg['id']))
    set_max_id(filename=filename, max_id=latest_id)
    waitapp()
