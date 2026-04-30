import urllib.request

url='http://127.0.0.1:8001/api/v1/servicos/?page=1&page_size=5'
req = urllib.request.Request(url, headers={'Accept':'application/json'})
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        print('Status', resp.status)
        print('Content-Type', resp.getheader('Content-Type'))
        data = resp.read().decode('utf8')
        print(data[:400])
except Exception as e:
    print('ERROR', e)
