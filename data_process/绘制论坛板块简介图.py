# coding:utf-8
import pandas as pd
import show_plot


def function():
    pairs = []
    node_map = {0: u"清水河畔"}
    data_frame = pd.read_csv("../data/bbs_stat/forum_tree_pic_data.csv", encoding="utf-8")
    for _, row in data_frame.iterrows():
        node_map[row["id"]] = u"%s" % row["name"]
        pairs.append((row["up"], row["id"]))
    show_plot.draw_director_tree(node_map, pairs, "bbs_zone_tree_example.png")


if __name__ == "__main__":
    function()
