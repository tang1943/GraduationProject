# coding:utf-8
# Author:yunya  Created: 2016/12/6
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

    @staticmethod
    def db_html_parse(item_id):
        base_url = "https://movie.douban.com/subject/%s/comments" % item_id
        url = "?sort=new_score"
        comments = []
        scores = []
        votes = []
        has_next = True
        retry = 0
        while has_next and retry < 4:
            try:
                req = urllib2.urlopen(base_url + url)
                print (base_url + url)
                retry = 0
            except urllib2.HTTPError, e:
                if e.code == 403:
                    has_next = False
                    continue
            except Exception, e:
                print "request error"
                print e
                retry += 1
                time.sleep(random.randint(30, 80) / 10.0)
                continue
            origin_encode = req.headers['content-type'].split('charset=')[-1]
            html = req.read().decode(origin_encode).encode("utf-8")
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
        return comments, scores, votes

    def run(self):
        while True:
            item_id = get_resource()
            if item_id is None:
                break
            print "%s crawler item:%s" % (self.crawler_name, item_id)
            comments, scores, votes = self.db_html_parse(item_id)
            df = pd.DataFrame({"cmt": comments,
                               "score": scores,
                               "vote": votes})
            df.to_csv('../data/movie_comments.csv', mode="a", index=False, encoding='utf-8', header=False)
            print "%s crawler item%s end" % (self.crawler_name, item_id)

resource_lock = Lock()
queue = Queue.Queue()


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
    with io.open("../data/movies_target.csv", "r", encoding="utf-8") as input_file:
        for line in input_file:
            groups = re.findall(r"(?<=https://movie\.douban\.com/subject/)[0-9]+(?=/,)", line)
            queue.put(groups[0])
    crawler1 = DBMovieCrawler("db1")
    crawler2 = DBMovieCrawler("db2")
    crawler3 = DBMovieCrawler("db3")
    crawler1.start()
    crawler2.start()
    crawler3.start()
