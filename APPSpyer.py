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
        os.mkdir(tmp)
    num = len(app_info_dict)
    pd_info = pd.DataFrame(app_info_dict).T
    file_name = "appInfo%s.xlsx"%pd.datetime.now().strftime('%Y%m%d%H%M%S')
    pd_info.to_excel(tmp+file_name)
    app_info_dict.clear()
    logger.info('成功保存 %d 条记录到文件 %s'%(num,file_name))


def parse_one(soup,burl,tmp):
    app_info_dict = defaultdict(lambda :defaultdict())
    info = soup.find(class_="app_list border_three").ul.find_all("li")
    for one in info:
        cc = len(app_info_dict)
        abc = one.find('div',{'class':'app_info'}).find('a')
        tmpurl = abc.get('href')
        app_name = abc.get_text()
        app_detail = get_url_content(burl+tmpurl)
        app_info=app_detail.find(class_="app_detail_infor").get_text()
        app_info_dict[cc]["app_name"]=app_name
        app_info_dict[cc]["app_url"]=burl+tmpurl
        app_info_dict[cc]["app_info"]=app_info
        for ll in app_detail.find(id="detail_line_ul").find_all("li"):
            ptext = ll.get_text()
            if "：" in ptext:
                ss = ptext.split("：")
                app_info_dict[cc][ss[0]]=ss[1]
        logger.info('%s OK'%app_name)
    save_file(app_info_dict,tmp)
    next = soup.find(class_="next").get('href')
    if next is None:
        return
    logger.info('下一页')
    del app_detail,abc,soup,app_info
    parse_one(get_url_content(burl+next),burl,tmp)


def get_url_list(soup,burl):
    innerLinks = set()
    ress = re.compile('\/sort.*')
    for one in soup.find_all('a',{'href':ress}):
        innerLinks.add(burl+one.get('href'))
    return innerLinks


def merge(tmp):
    fs = [tmp+f for f in os.listdir(tmp) if f.split('.')[1] == 'xlsx']
    if fs == []:
        return
    df = pd.concat(map(lambda x: pd.read_excel(x),fs),ignore_index=True)
    df.to_excel('appInfo.xlsx')


def main():
    burl = "http://www.anzhi.com"
    base_url = '/applist.html'
    tmp = 'tmp/'
    innerLinks = get_url_list(get_url_content(burl+base_url),burl)
    for u in innerLinks:
        parse_one(get_url_content(u),burl,tmp)
    merge(tmp)


if __name__ == "__main__":
    main()
