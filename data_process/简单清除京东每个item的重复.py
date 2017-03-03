# coding:utf-8

data = {}
f = open("../data/crawler/jd_target_origin.csv", "r")
for line in f:
    items = line.strip().split(",")
    # 晒掉差评小于5的商品
    if int(items[-1]) < 5:
        continue
    group = data.get(items[0], [])
    group.append((items[1], ",".join(items[2:])))
    data[items[0]] = group
f.close()
f = open("../data/crawler/jd_target.csv", "w")
for key in data:
    u = {}
    for d in data[key]:
        u[d[1]] = d[0]
    for key_ in u:
        f.write("%s,%s,%s\n" % (key, u[key_], key_))
f.close()
