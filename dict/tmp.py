# coding:utf-8

f1 = open("word_dict.txt", "r")
s = set()
for line in f1:
    line = line.strip()
    if line != "":
        s.add(line)
f1.close()
f2 = open("word_dict2.txt", "w")
for key in s:
    f2.write("%s\n" % key)
f2.close()
