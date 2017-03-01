# coding:utf-8
"""
爬去不同类目下的京东商品ID
"""
import pandas as pd
import urllib2
import Queue
import random
import time
import re
import json
import threading
from threading import Lock
from bs4 import BeautifulSoup
import socket


class JDItemInfoCrawler(threading.Thread):

    crawler_name = "default"

    def __init__(self, name):
        super(JDItemInfoCrawler, self).__init__()
        socket.setdefaulttimeout(16)
        self.crawler_name = name

    def db_html_parse(self, item_id):
        url = "https://sclub.jd.com/comment/productPageComments.action?productId=%s&score=0&sortType=3&page=0" \
              "&pageSize=10&callback=fetchJSON_comment98vv37464" % item_id
        while True:
            try:
                random_user_agent = random.choice(agents)
                random_proxy = get_proxy()
                proxy_support = urllib2.ProxyHandler({"https": random_proxy})
                opener = urllib2.build_opener(proxy_support)
                opener.addheaders = [('User-Agent', random_user_agent)]
                start_time = time.time()
                print "%s:start open web page..." % self.crawler_name
                req = opener.open(url, None, 16)
                print "%s load complete:%s" % (self.crawler_name, url)
                print time.time() - start_time
                origin_encode = req.headers['content-type'].split('charset=')[-1]
                html = req.read().decode(origin_encode).encode("utf-8")
                if html.strip() == "":
                    raise Exception("get empty html")
                soup = BeautifulSoup(html, "html.parser")

                if len(soup.select("div#db-nav-movie")) < 1:
                    raise Exception("enter fake douban website")
                add_proxy_info(random_proxy, True)
                groups = re.findall("(?<=fetchJSON_comment98vv37464\().*(?=\);)", html)
                if len(groups) > 0:
                    o = json.loads(groups[0], encoding="utf-8")
                    return "%d,%d,%d,%d,%d,%d" % (o["maxPage"], o["productCommentSummary"]["afterCount"],
                                                  o["productCommentSummary"]["commentCount"],
                                                  o["productCommentSummary"]["goodCount"],
                                                  o["productCommentSummary"]["generalCount"],
                                                  o["productCommentSummary"]["poorCount"])
                else:
                    return None
            except urllib2.HTTPError, e:
                    print "%s get the http error:%s" % (self.crawler_name, url)
                    print e
            except urllib2.URLError, e:
                print "%s:url error %s" % (self.crawler_name, str(e))
                print "%s:change proxy ip" % self.crawler_name
                if e.reason.errno != 10060 and e.reason.errno != 110:
                    add_proxy_info(random_proxy, False)
            except Exception, e:
                print "%s:other error %s" % (self.crawler_name, str(e))
                add_proxy_info(random_proxy, False)

    def run(self):
        while True:
            item_id = get_resource()
            if item_id is None:
                break
            print "%s crawler item:%s" % (self.crawler_name, item_id)
            movie_ids, comment_ids, comments, scores, votes = self.db_html_parse(item_id)
            df = pd.DataFrame({
                "id": movie_ids,
                "cmt_id": comment_ids,
                "cmt": comments,
                "score": scores,
                "vote": votes})
            save_comments(df)
            save_complete_record(item_id, len(movie_ids))
            complete_set.add(item_id)
            print "%s crawler item%s end with %d items" % (self.crawler_name, item_id, len(movie_ids))
            print "proxy pool size: %d" % len(proxies)


url_pool_lock = Lock()
comment_save_lock = Lock()
task_end_save_lock = Lock()
queue = Queue.Queue()
proxies = {}
agents = []
complete_set = set()


# 管理代理IP
class ProxyManager(threading.Thread):

    sleep_time = 120

    def __init__(self, sleep_time):
        super(ProxyManager, self).__init__()
        self.sleep_time = sleep_time

    def run(self):
        while queue.qsize() > 0:
            time.sleep(self.sleep_time)
            if len(proxies) > 600:
                pop_key = []
                for key, data in proxies.items():
                    if data["total"] > 100 and (data["catch"] * 1.0 / data["total"]) < 0.03:
                        pop_key.append(key)
                for key in pop_key:
                    proxies.pop(key)
                print "========================================"
                print "proxy remain: %d" % len(proxies)
                print "========================================"
            else:
                print "========================================"
                print "too less proxies manager exit"
                print "========================================"
                break


def add_proxy_info(key, is_success):
    try:
        if is_success:
            proxies[key]["catch"] += 1
        proxies[key]["total"] += 1
    except Exception, e:
        print e
        print "add info to deleted proxy"


def get_proxy():
    return random.choice(proxies.keys())


def get_resource():
    url_pool_lock.acquire()
    if queue.empty():
        url_pool_lock.release()
        return None
    r = queue.get()
    print "url remain: %d" % queue.qsize()
    url_pool_lock.release()
    return r


def save_comments(str):
    comment_save_lock.acquire()
    with open("jd_target.csv", "a") as f:
        f.write(str)
    comment_save_lock.release()


def save_complete_record(complete_url):
    task_end_save_lock.acquire()
    with open("jd_url_complete.csv", "a") as complete_file:
        complete_file.write("%s\n" % complete_url)
    task_end_save_lock.release()

if __name__ == "__main__":
    unique_proxies = set()
    with open("proxy_ip", "r") as proxy_file:
        for line in proxy_file:
            unique_proxies.add(line.strip())
    for proxy_address in unique_proxies:
        proxies[proxy_address] = {"total": 0, "catch": 0}
    with open("user_agent", "r") as agent_file:
        for line in agent_file:
            agents.append(line.strip())
    with open("jd_url_complete.csv", "r") as end_file:
        for line in end_file:
            complete_set.add(int(line.split(",")[0]))
    all_items = open("../data/crawler/JDCategoryURL.csv", "r")
    for u in all_items:
        if u not in complete_set:
            queue.put(u)
    for i in range(32):
        crawler = JDItemInfoCrawler("jd" + str(i))
        crawler.start()
    ProxyManager(60).start()



