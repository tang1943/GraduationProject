# coding:utf-8
import pandas as pd
import urllib2
import Queue
import gc
import random
import time
import threading
from threading import Lock
from bs4 import BeautifulSoup
import socket


class DBMovieCrawler(threading.Thread):

    crawler_name = "default"
    opener = None
    random_proxy = None

    def __init__(self, name):
        super(DBMovieCrawler, self).__init__()
        socket.setdefaulttimeout(16)
        self.crawler_name = name
        self.change_proxy()

    def change_proxy(self):
        random_user_agent = random.choice(agents)
        self.random_proxy = get_proxy()
        proxy_support = urllib2.ProxyHandler({"https": self.random_proxy})
        # proxy_support = urllib2.ProxyHandler()
        self.opener = urllib2.build_opener(proxy_support)
        self.opener.addheaders = [('User-Agent', random_user_agent)]

    def db_html_parse(self, item_id):
        base_url = "https://movie.douban.com/subject/%s/comments" % item_id
        url = "?sort=new_score"
        comments = []
        scores = []
        votes = []
        movie_ids = []
        data_ids = []
        has_next = True
        retry = 0
        while has_next:
            try:
                start_time = time.time()
                print "%s:start open web page..." % self.crawler_name
                req = self.opener.open(base_url + url, None, 16)
                print "%s load complete:%s%s" % (self.crawler_name, base_url, url)
                print time.time() - start_time
                origin_encode = req.headers['content-type'].split('charset=')[-1]
                html = req.read()
                req.close()
                self.opener.close()
                if html.strip() == "":
                    raise Exception("get empty html")
                html = html.decode(origin_encode, "ignore").encode("utf-8")
                soup = BeautifulSoup(html, "html.parser")
                if len(soup.select("div#db-nav-movie")) < 1:
                    raise Exception("enter fake douban website")
                retry = 0
                add_proxy_info(self.random_proxy, True)
            except urllib2.HTTPError, e:
                if e.code == 403 and retry >= 2:
                    print "%s get the end:%s%s" % (self.crawler_name, base_url, url)
                    has_next = False
                else:
                    self.change_proxy()
                    retry += 1
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
            body_divs = soup.select("div.article")
            if len(body_divs) > 0:
                comment_body_divs = body_divs[0].select("div#comments")
                if len(comment_body_divs) > 0:
                    comment_body = comment_body_divs[0]
                    for comment_div in comment_body.select("div.comment-item"):
                        rating_spans = comment_div.select("span.rating")
                        if len(rating_spans) < 1:
                            continue
                        scores.append(rating_spans[0]["class"][0][-2:-1])
                        votes.append(int(comment_div.select("span.votes")[0].text))
                        comments.append(comment_div.select("div.comment > p.")[0].text.strip())
                        movie_ids.append(item_id)
                        data_ids.append(comment_div["data-cid"])
                    paginator_divs = body_divs[0].select("div#paginator")
                    if len(paginator_divs) > 0:
                        next_divs = paginator_divs[0].select("a.next")
                        if len(next_divs) > 0:
                            url = next_divs[0]["href"]
                        else:
                            has_next = False
                    else:
                        has_next = False
                else:
                    has_next = False
            else:
                has_next = False
        return movie_ids, data_ids, comments, scores, votes

    def run(self):
        while True:
            item_id = get_resource()
            if item_id is None:
                break
            print "%s crawler item:%s" % (self.crawler_name, item_id)
            movie_ids, comment_ids, comments, scores, votes = self.db_html_parse(item_id)
            save_comments({
                "id": movie_ids,
                "cmt_id": comment_ids,
                "cmt": comments,
                "score": scores,
                "vote": votes})
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
    print "url remain: %d" % queue.qsize()
    url_pool_lock.release()
    return r


def save_comments(data):
    df = pd.DataFrame(data)
    comment_save_lock.acquire()
    with open("movie_comments.csv", "a") as output_file:
        df.to_csv(output_file, mode="a", index=False, encoding='utf-8', header=False)
    comment_save_lock.release()


def save_complete_record(item_id, size):
    task_end_save_lock.acquire()
    with open("douban_complete.csv", "a") as complete_file:
        complete_file.write("%s,%d\n" % (item_id, size))
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
    complete_set = set()
    with open("douban_complete.csv", "r") as end_file:
        for line in end_file:
            complete_set.add(int(line.split(",")[0]))
    all_items = pd.read_csv("movies_target.csv", encoding="utf-8")
    for m_id in all_items.get("id"):
        if m_id not in complete_set:
            queue.put(m_id)
    for i in range(60):
        crawler = DBMovieCrawler("db" + str(i))
        crawler.start()
    ProxyManager(120).start()



