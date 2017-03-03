# coding:utf-8
import pandas as pd
import Queue
import show_plot


items = {}
tree = {0: {}}


def function():
    pairs = []
    node_map = {0: u"清水河畔"}
    data_frame = pd.read_csv("../data/forum.csv", encoding="utf-8")
    for _, row in data_frame.iterrows():
        node_map[row["id"]] = u"%s%s\n%s\n%s" % (row["id"], row["name"], row["thread"], row["category"])
        pairs.append((row["up"], row["id"]))
    show_plot.draw_director_tree(node_map, pairs)


def function2():
    # id, up, type, name, category, thread, post
    record = 0
    data_frame = pd.read_csv("../data/forum.csv", encoding="utf-8")
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

if __name__ =="__main__":
    function2()
