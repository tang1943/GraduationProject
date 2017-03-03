# coding:utf-8
"""
爬去不同类目下的京东商品ID
"""
import pandas as pd
import urllib2
import Queue
import gc
import random
import time
import re
import json
import threading
from threading import Lock
import socket


class JDItemCrawler(threading.Thread):

    crawler_name = "default"
    opener = None
    random_proxy = None
    url = "https://sclub.jd.com/comment/productPageComments.action?productId=%s&score=%d&sortType=5&page=%d" \
          "&pageSize=10&callback=fetchJSON_comment98vv37464"

    def __init__(self, name):
        super(JDItemCrawler, self).__init__()
        socket.setdefaulttimeout(16)
        self.crawler_name = name
        self.change_proxy()

    def change_proxy(self):
        random_user_agent = random.choice(agents)
        self.random_proxy = get_proxy()
        proxy_support = urllib2.ProxyHandler({"https": self.random_proxy})
        self.opener = urllib2.build_opener(proxy_support)
        self.opener.addheaders = [('User-Agent', random_user_agent)]

    def jd_html_parse(self, item_id, pages):
        comments_storage, scores_storage = [], []
        useful_vote_storage, useless_vote_storage = [], []
        reply_count_storage, image_count_storage = [], []
        user_level_storage, father_ids, ids = [], [], []
        for score, count in zip(range(1, 4), pages):
            for page in range(count):
                complete = False
                while not complete:
                    try:
                        start_time = time.time()
                        print "%s:start open web page..." % self.crawler_name
                        target_url = self.url % (item_id, score, page)
                        req = self.opener.open(target_url, None, 16)
                        print "%s load complete:%s" % (self.crawler_name, target_url)
                        print time.time() - start_time
                        origin_encode = req.headers['content-type'].split('charset=')[-1]
                        html = req.read()
                        req.close()
                        self.opener.close()
                        if html.strip() == "":
                            raise Exception("get empty html")
                        html = html.decode(origin_encode, "ignore").encode("utf-8")
                        if "fetchJSON_comment98vv37464" not in html:
                            raise Exception("enter fake jd return")
                        add_proxy_info(self.random_proxy, True)
                        groups = re.findall("(?<=fetchJSON_comment98vv37464\().*(?=\);)", html)
                        if len(groups) > 0:
                            for group in groups:
                                json_item = json.loads(group, encoding="utf-8")
                                if json_item["comments"] is not None:
                                    for comment in json_item["comments"]:
                                        father_ids.append(item_id)
                                        ids.append(comment["id"])
                                        comments_storage.append(comment["content"].strip())
                                        scores_storage.append(comment["score"])
                                        useful_vote_storage.append(comment["usefulVoteCount"])
                                        useless_vote_storage.append(comment["uselessVoteCount"])
                                        reply_count_storage.append(comment["replyCount"])
                                        if "imageCount" in comment:
                                            image_count_storage.append(comment["imageCount"])
                                        else:
                                            image_count_storage.append(0)
                                        user_level_storage.append(comment["userLevelId"])
                        complete = True
                    except urllib2.HTTPError, e:
                            print "%s get the http error:%s" % (self.crawler_name, target_url)
                            print e
                            self.change_proxy()
                            continue
                    except urllib2.URLError, e:
                        print "%s:url error %s" % (self.crawler_name, str(e))
                        print "%s:change proxy ip" % self.crawler_name
                        if e.reason.errno != 10060 and e.reason.errno != 110:
                            add_proxy_info(self.random_proxy, False)
                        self.change_proxy()
                        continue
                    except Exception, e:
                        print "%s:other error %s" % (self.crawler_name, str(e))
                        add_proxy_info(self.random_proxy, False)
                        self.change_proxy()
                        continue
        return {
            "item_id": father_ids,
            "id": ids,
            "comment": comments_storage,
            "score": scores_storage,
            "useful": useful_vote_storage,
            "use_less": useless_vote_storage,
            "image": image_count_storage,
            "reply": reply_count_storage,
            "user_level": user_level_storage
        }

    def run(self):
        while True:
            task = get_resource()
            if task is None or len(task) < 4:
                break
            item_id = task[0]
            bad_page = int(task[-1]) / 10
            limit_page = int(2.2 * bad_page)
            general_page = int(task[-2]) / 10
            good_page = int(task[-3]) / 10
            general_page = general_page if general_page < limit_page else limit_page
            good_page = good_page if good_page < limit_page else limit_page
            bad_page += 1
            general_page += 1
            good_page += 1
            print "%s crawler item:%s" % (self.crawler_name, item_id)
            data = self.jd_html_parse(item_id, [bad_page, general_page, good_page])
            save_result(data)
            save_complete_record(item_id)
            print "%s crawler item:%s end" % (self.crawler_name, item_id)
            print "proxy pool size: %d" % len(proxies)


url_pool_lock = Lock()
comment_save_lock = Lock()
task_end_save_lock = Lock()
queue = Queue.Queue()
proxies = {}
agents = []
columns = ["item_id", "id", "comment", "image", "reply", "score", "use_less", "useful", "user_level"]


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
                    if data["total"] > 100 and (data["catch"] * 1.0 / data["total"]) < 0.10:
                        pop_key.append(key)
                for key in pop_key:
                    proxies.pop(key)
                print "========================================"
                print "proxy remain: %d" % len(proxies)
                print "========================================"
            gc.collect()


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
    url_pool_lock.release()
    print "url remain: %d" % queue.qsize()
    return r


def save_result(data):
    df = pd.DataFrame(data)
    comment_save_lock.acquire()
    with open("jd_comments.csv", "a") as output_file:
        df.to_csv(output_file, mode="a", index=False, encoding='utf-8', header=False, columns=columns)
    comment_save_lock.release()


def save_complete_record(complete_id):
    task_end_save_lock.acquire()
    with open("jd_complete.csv", "a") as complete_file:
        complete_file.write("%s\n" % complete_id)
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
    used_set = set()
    with open("jd_complete.csv", "r") as used_f:
        for line in used_f:
            used_set.add(line.strip())
    all_items = open("jd_target.csv", "r")
    for line in all_items:
        items = line.strip().split(",")
        if len(items) > 7 and items[1] not in used_set:
            queue.put((items[1], items[-3], items[-2], items[-1]))
    for i in range(512):
        crawler = JDItemCrawler("jd" + str(i))
        crawler.start()
    ProxyManager(120).start()




