# coding:utf-8
import pandas as pd
import Queue
import show_plot


items = {}
tree = {0: {}}


def draw_all():
    pairs = []
    node_map = {0: u"清水河畔"}
    data_frame = pd.read_csv("../data/bbs/forum.csv", encoding="utf-8")
    for _, row in data_frame.iterrows():
        node_map[row["id"]] = u"%s%s\n%s\n%s" % (row["id"], row["name"], row["thread"], row["category"])
        # node_map[row["id"]] = u"%s" % row["name"]
        pairs.append((row["up"], row["id"]))
    show_plot.draw_director_tree(node_map, pairs, "all_zone.png")


# 统计每个板块的数量
def stat_zone():
    # id, up, type, name, category, thread, post
    record = 0
    data_frame = pd.read_csv("../data/bbs/forum.csv", encoding="utf-8")
    f = set([0])
    level = 0
    data = {}
    while record < len(data_frame):
        son = set()
        for _, row in data_frame.iterrows():
            if row["up"] in f:
                data[row["name"]] = level
                son.add(row["id"])
                record += 1
        level += 1
        f = son
    stat = [[], [], [], []]
    for key in data:
        stat[data[key]].append(key)
    print len(stat[0])
    print len(stat[1])
    print len(stat[2])
    print len(stat[3])

if __name__ == "__main__":
    # 统计每级板块的数量
    # stat_zone()
    # 绘制整个板块图
    draw_all()
