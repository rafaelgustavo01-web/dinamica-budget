import urllib.request
openapi_url='http://127.0.0.1:8001/openapi.json'
try:
    with urllib.request.urlopen(openapi_url, timeout=30) as resp:
        data=resp.read().decode('utf8')
        print('Has /api/v1/servicos:', '/api/v1/servicos' in data)
        print('Has /api/v1/bcu:', '/api/v1/bcu' in data)
        # print available paths snippet
        print('\nPaths snippet:', data[data.find('"paths"')-10:data.find('"paths"')+200])
except Exception as e:
    print('ERROR', e)
