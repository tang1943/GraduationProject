# encoding=utf8
import urllib
import socket
socket.setdefaulttimeout(3)
f = open("proxy_ip", "r")
w = open("proxy_effect", "w")
lines = f.readlines()
proxys = []
for i in range(0, len(lines)):
    proxy_host = "http://" + lines[i].strip("\n")
    proxy_temp = {"http": proxy_host}
    proxys.append(proxy_temp)
url = "http://ip.chinaz.com/getip.aspx"
for proxy in proxys:
    try:
        res = urllib.urlopen(url,proxies=proxy).read()
        if "{ip:" in res and ",address:" in res and "223.87.232.50" not in res:
            print res
            w.write(proxy['http'] + "\n")
    except Exception,e:
        e.message
        # print proxy
        # print e
        # continue
w.close()