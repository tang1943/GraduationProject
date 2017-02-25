# coding:utf-8

import pandas as pd
import re
import sys


def delete_new_line_char(input_str):
    return re.sub(r"(\r\n|\r|\n)", "", input_str)


if __name__ == "__main__":
    # 处理京东评论
    comment_file = open("../data/comment.csv", "r")
    comment_out = open("../data/comment_out.csv", "w")
    for line in comment_file:
        if line[0:1] == '"':
            if len(set(line[1:-4])) < 4 and "好" not in line and "好" not in line and "赞" not in line \
                    and "棒" not in line and "贵" not in line and "ok" not in line and "OK" not in line \
                    and "Ok" not in line and "hao" not in line and "哈" not in line and "good" not in line:
                print line
            else:
                comment_out.write(line)
        else:
            if len(set(line[0:-3])) < 4 and "好" not in line and "差" not in line and "赞" not in line \
                    and "棒" not in line and "贵" not in line and "ok" not in line and "OK" not in line \
                    and "Ok" not in line and "hao" not in line and "哈" not in line and "good" not in line:
                print line
            else:
                comment_out.write(line)
            # print
    #
    # print score_set
    # data_frame = pd.read_csv("../data/comment.csv", encoding="utf-8")
    # for index, row in data_frame.iterrows():
    #     if len(set(row["cmt"])) < 2:
    #         data_frame.drop(index)
    # data_frame.to_csv('../data/jd_clean.csv', mode="a", index=False, encoding='utf-8', header=True)
