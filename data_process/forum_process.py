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


    # queue = Queue.Queue()
    # queue.put(0)
    # items[0] = {}
    # while not queue.empty():
    #     father_id = queue.get()
    #     father = tree
    #     for key, item in items.items():
    #         if item['up'] == father_id:


if __name__ =="__main__":
    function()
