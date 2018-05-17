# coding=utf-8
from collections import defaultdict
from bs4 import BeautifulSoup
from urllib.request import urlopen
from functools import reduce
import time
import re
import pandas as pd
import logging
import sys
import os


logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)
fmt = logging.Formatter('%(asctime)s %(levelname)-8s:%(message)s')
fh = logging.FileHandler('%s.log'%(__file__.split('.')[0]))
fh.setFormatter(fmt)
logger.addHandler(fh)
sh = logging.StreamHandler(sys.stdout)
sh.setFormatter(fmt)
logger.addHandler(sh)


logger_record = logging.getLogger(__file__+'2')
logger_record.setLevel(logging.INFO)
fh2 = logging.FileHandler('working_page.log')
fh2.setFormatter(fmt)
logger_record.addHandler(fh2)


logger_big = logging.getLogger(__file__+'3')
logger_big.setLevel(logging.INFO)
fh3 = logging.FileHandler('working_run.log')
logger_big.addHandler(fh3)


def bsgo(func):
    def f(*arg,**kw):
        return BeautifulSoup(func(*arg,**kw), 'html.parser')
    return f


@bsgo
def get_url_content(url):
    time.sleep(3)
    return urlopen(url)


def save_file(app_info_dict,tmp):
    if not os.path.exists(tmp):
        os.makedirs(tmp)
    num = len(app_info_dict)
    pd_info = pd.DataFrame(app_info_dict).T
    file_name = "appInfo%s.xlsx"%pd.datetime.now().strftime('%Y%m%d%H%M%S')
    pd_info.to_excel(tmp+file_name)
    logger.info('成功保存%d条记录到文件:%s'%(num,file_name))
    app_info_dict.clear()


def get_working_page():
    logname = 'working_page.log'
    if not os.path.exists(logname) or not os.path.getsize(logname):
        return None
    with open(logname,'rb') as f:
        pos = -1
        while True:
            pos = pos - 1
            try:
                f.seek(pos, 2)  #从文件末尾开始读
                if f.read(1) == b'\n':
                    break
            except:     #到达文件第一行，直接读取，退出
                f.seek(0, 0)
                return str(f.readline().strip()[33:])
        return str(f.readline().strip()[33:], encoding = "utf-8")


def get_finish_run():
    logname = 'working_run.log'
    f = open(logname)
    return set([l.strip() for l in f.readlines()])


def parse_one(soup,burl,tmp):
    app_info_dict = defaultdict(lambda :defaultdict())
    info = soup.find(class_="app_list border_three").ul.find_all("li")
    cc = 0
    for one in info:
        cc += 1
        if cc == 3:
            break
        abc = one.find('div',{'class':'app_info'}).find('a')
        tmpurl = abc.get('href')
        app_name = abc.get_text()
        app_detail = get_url_content(burl+tmpurl)
        app_info = app_detail.find(class_="app_detail_infor").get_text()
        app_info_dict[tmpurl]["app_name"] = app_name
        app_info_dict[tmpurl]["app_url"] = burl+tmpurl
        app_info_dict[tmpurl]["app_info"] = app_info
        for ll in app_detail.find(id="detail_line_ul").find_all("li"):
            ptext = ll.get_text()
            if "：" in ptext:
                ss = ptext.split("：")
                app_info_dict[tmpurl][ss[0]] = ss[1]
        logger.info('%s OK'%app_name)
    save_file(app_info_dict,tmp)
    next = soup.find(class_="next").get('href')
    if next is None:
        return
    del app_detail,abc,soup,app_info
    logger.info('下一页')
    logger_record.info('%s'%(burl+next))
    parse_one(get_url_content(burl+next),burl,tmp)


def get_url_list(soup,burl):
    innerLinks = set()
    ress = re.compile('\/sort.*')
    for one in soup.find_all('a',{'href':ress}):
        innerLinks.add(burl+one.get('href'))
    finishLinks = get_finish_run()
    innerLinks = list(innerLinks - finishLinks)
    innerLinks.sort()
    return innerLinks


def merge(tmp):
    fs = [tmp+f for f in os.listdir(tmp) if f.split('.')[1] == 'xlsx']
    if fs == []:
        return
    df = pd.concat(map(lambda x: pd.read_excel(x),fs))
    df.to_excel(tmp+'appInfo.xlsx')


def main():
    burl = "http://www.anzhi.com"
    base_url = '/applist.html'
    game_url = '/gamelist.html'
    innerLinks = get_url_list(get_url_content(burl+game_url),burl)
    last_working = get_working_page()
    first = True
    for u in innerLinks:
        if first and last_working:
            u = last_working
            first = False
        tmp = 'tmp/tmp_%s/'%u[21:28]
        parse_one(get_url_content(u),burl,tmp)
        logger_big.info(u)
        merge(tmp)


def trytrytry(m,n):
    if m == 0:
        return
    try:
        main()
    except Exception as e:
        logger.error('%d:%s'%(n,e))
        time.sleep(60)
        trytrytry(m-1,n+1)


if __name__ == "__main__":
    trytrytry(10,1)
