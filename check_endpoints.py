import urllib.request
import sys
paths=['/payments/','/find-my-car/']
for p in paths:
    url='http://127.0.0.1:8000'+p
    try:
        req=urllib.request.Request(url, method='HEAD')
        r=urllib.request.urlopen(req, timeout=5)
        print(p, r.getcode())
    except Exception as e:
        print(p, 'ERROR', repr(e))
