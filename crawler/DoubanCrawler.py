# coding:utf-8
import pandas as pd
import urllib2
import re
import io
import Queue
import random
import time
import threading
from threading import Lock
from bs4 import BeautifulSoup


class DBMovieCrawler(threading.Thread):

    crawler_name = "default"

    def __init__(self, name):
        super(DBMovieCrawler, self).__init__()
        self.crawler_name = name

    def db_html_parse(self, item_id):
        random_user_agent = random.choice(agents)
        random_proxy = random.choice(proxies)
        base_url = "https://movie.douban.com/subject/%s/comments" % item_id
        url = "?sort=new_score"
        comments = []
        scores = []
        votes = []
        movie_ids = []
        data_ids = []
        has_next = True
        retry = 0
        first_page = True
        while has_next and retry < 4:
            try:
                # 下面是模拟浏览器进行访问
                # req = urllib2.Request(base_url + url)
                # req.add_header("User-Agent", random_user_agent)
                # 下面是使用ip代理进行访问
                proxy_support = urllib2.ProxyHandler({"https": random_proxy})
                opener = urllib2.build_opener(proxy_support)
                opener.addheaders = [('User-Agent', random_user_agent)]
                # urllib2.install_opener(opener)
                req = opener.open(base_url + url, timeout=4000)
                print "%s:%s%s" % (self.crawler_name, base_url, url)
                retry = 0
                first_page = False
            except urllib2.HTTPError, e:
                if e.code == 403 and retry >= 3:
                    has_next = False
                    continue
                else:
                    random_user_agent = random.choice(agents)
                    random_proxy = random.choice(proxies)
                    retry += 1
            except urllib2.URLError, e:
                print "%s:url error" % self.crawler_name
                print e
                print "%s:change proxy ip" % self.crawler_name
                if e.reason.errno != 10060:
                    print "%s:remove proxy ip" % self.crawler_name
                    proxies.remove(random_proxy)
                random_proxy = random.choice(proxies)
                continue
            except Exception, e:
                print "other error"
                print e
                print "%s:remove proxy ip" % self.crawler_name
                proxies.remove(random_proxy)
                random_proxy = random.choice(proxies)
                continue
            origin_encode = req.headers['content-type'].split('charset=')[-1]
            html = req.read().decode(origin_encode).encode("utf-8")
            print "load complete"
            soup = BeautifulSoup(html, "html.parser")
            body_divs = soup.select("div.article")
            if len(body_divs) > 0:
                comment_body_divs = body_divs[0].select("div#comments")
                if len(comment_body_divs) > 0:
                    comment_body = comment_body_divs[0]
                    for comment_div in comment_body.select("div.comment-item"):
                        rating_spans = comment_div.select("span.rating")
                        if len(rating_spans) < 1:
                            continue
                        scores.append(rating_spans[0]["class"])
                        votes.append(int(comment_div.select("span.votes")[0].text))
                        comments.append(comment_div.select("div.comment > p.")[0].text)
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
            time.sleep(random.randint(5, 15) / 10.0)
        return movie_ids, data_ids, comments, scores, votes

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
            df.to_csv('../data/movie_comments.csv', mode="a", index=False, encoding='utf-8', header=False)
            print "%s crawler item%s end with %d items" % (self.crawler_name, item_id, len(movie_ids))

resource_lock = Lock()
queue = Queue.Queue()
proxies = []
agents = []


def get_resource():
    resource_lock.acquire()
    if queue.empty():
        resource_lock.release()
        return None
    r = queue.get()
    print "remain: %d" % queue.qsize()
    resource_lock.release()
    return r

if __name__ == "__main__":
    with open("proxy_ip", "r") as proxy_file:
        for line in proxy_file:
            proxies.append(line.strip())
    with open("user_agent", "r") as agent_file:
        for line in agent_file:
            agents.append(line.strip())
    with io.open("../data/movies_target.csv", "r", encoding="utf-8") as input_file:
        for line in input_file:
            groups = re.findall(r"(?<=https://movie\.douban\.com/subject/)[0-9]+(?=/,)", line)
            queue.put(groups[0])
    crawler1 = DBMovieCrawler("db1")
    # crawler2 = DBMovieCrawler("db2")
    # crawler3 = DBMovieCrawler("db3")
    crawler1.start()
    # crawler2.start()
    # crawler3.start()
