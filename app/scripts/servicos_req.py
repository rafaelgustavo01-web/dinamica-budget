import urllib.request
resp = urllib.request.urlopen('http://127.0.0.1:8001/api/v1/servicos/?page=1&page_size=5', timeout=30)
print(resp.status)
print(resp.getheader('Content-Type'))
print(resp.read()[:200])
