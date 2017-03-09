# coding:utf-8

import pandas as pd
import matplotlib.pyplot as plt
import pylab
import numpy as np
df = pd.read_csv("../data/bbs_stat/content_length.csv", encoding="utf-8")

x = ["0-50", "50-100", "100-500", "500-1000", "1000-2000", "2000-3000", ">3000"]
y = [0, 0, 0, 0, 0, 0, 0]
for _, row in df.iterrows():
    if 0 <= row["length"] < 50:
        # x.append(row["length"])
        y[0] += row["count"]
    elif 50 <= row["length"] < 100:
        y[1] += row["count"]
    elif 100 <= row["length"] < 500:
        y[2] += row["count"]
    elif 500 <= row["length"] < 1000:
        y[3] += row["count"]
    elif 1000 <= row["length"] < 2000:
        y[4] += row["count"]
    elif 2000 <= row["length"] < 3000:
        y[5] += row["count"]
    else:
        y[6] += row["count"]
index = np.arange(len(y))
bar_width = 0.35
rects = plt.bar(index, y, color="black")
plt.xticks(index + bar_width, x)
plt.title(u"bbs message length stat")
# rects.set_edgecolor('white')
plt.savefig("test.png")
plt.show()