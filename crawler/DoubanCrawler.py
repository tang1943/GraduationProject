# coding:utf-8
# Author:yunya  Created: 2016/12/6
import pandas as pd
import urllib2
import re
import random
import time
import json
import threading


class DBMovieCrawler(threading.Thread):

    scores = None
    item_ids = None
    crawler_name = "default"
    start_index = -1

    def __init__(self, item_ids_input, scores_input, start_index, name):
        super(DBMovieCrawler, self).__init__()
        self.item_ids = item_ids_input
        self.scores = scores_input
        self.crawler_name = name
        self.start_index = start_index

    @staticmethod
    def db_html_parse(item_id, score):
        url = "https://movie.douban.com/subject/%s/comments?sort=new_score" % item_id
        try:
            req = urllib2.urlopen(url)
        except Exception, e:
            print e
            return []
        origin_encode = req.headers['content-type'].split('charset=')[-1]
        try:
            html = req.read().decode(origin_encode).encode("utf-8")
            groups = re.findall("(?<=fetchJSON_comment98vv37464\().*(?=\);)", html)
            return [json.loads(group, encoding="utf-8") for group in groups]
        except Exception, e:
            print e
            return []

    def run(self):
        item_ids_to_crawler = self.item_ids[self.start_index:]
        for item_id in item_ids_to_crawler:
            print "%s crawler item%d" % (self.crawler_name, self.start_index)
            # 采集第一个关于各种评论的数量
            first_page = self.jd_html_parse(item_id, self.scores[0], 0)
            if len(first_page) < 1:
                continue
            page_count = min(
                first_page[0]["productCommentSummary"]["goodCount"] / 10,
                first_page[0]["productCommentSummary"]["generalCount"] / 10,
                first_page[0]["productCommentSummary"]["poorCount"] / 10)
            page_count = page_count if page_count < 150 else 150
            comments_storage, scores_storage = [], []
            for score in self.scores:
                print "Get score=%d" % score
                for page_index in range(page_count):  # 12.13 edit
                    for json_item in self.jd_html_parse(item_id, score, page_index):
                        try:
                            for comment in json_item["comments"]:
                                comment_content = comment["content"]
                                comment_content = comment_content.strip()
                                comment_content = comment_content.replace("\n", " ")
                                comment_content = re.sub(r'\s{2,}', " ", comment_content)
                                if len(comment_content) < 3:
                                    continue
                                comments_storage.append(comment_content)
                                scores_storage.append(comment["score"])
                        except Exception, e:
                            print e
                    time.sleep(random.randint(5, 10) / 10.0)
            df = pd.DataFrame({"cmt": comments_storage,
                               "score": scores_storage})
            df.to_csv('jd.csv', mode="a", index=False, encoding='utf-8', header=False)
            print "%s crawler item%d end" % (self.crawler_name, self.start_index)
            self.start_index += 1


if __name__ == "__main__":
    item_ids = ['25755645']

    scores = [1, 2, 3]
    crawler1 = DBMovieCrawler(item_ids, scores, 0, "db1")
    # crawler2 = JDCrawler(item_ids[1025:1060], scores, 0, "jd2")
    # crawler3 = JDCrawler(item_ids[732:1025], scores, 249, "jd3")
    crawler1.start()
    # crawler2.start()
    # crawler3.start()
