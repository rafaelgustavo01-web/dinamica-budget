import json
import urllib.request
from pathlib import Path

env = Path(__file__).parents[1] / '.env'
if not env.exists():
    print('Missing app/.env')
    raise SystemExit(1)
text = env.read_text(encoding='utf8')
creds = {}
for line in text.splitlines():
    if '=' in line and not line.strip().startswith('#'):
        k,v = line.split('=',1)
        creds[k.strip()]=v.strip()
email = creds.get('ROOT_USER_EMAIL')
password = creds.get('ROOT_USER_PASSWORD')
if not email or not password:
    print('ROOT_USER_EMAIL or ROOT_USER_PASSWORD missing in app/.env')
    raise SystemExit(1)

base = 'http://127.0.0.1:8001/api/v1'
# login
login_url = base + '/auth/login'
login_data = json.dumps({'email': email, 'password': password}).encode('utf8')
req = urllib.request.Request(login_url, data=login_data, headers={'Content-Type':'application/json'})
try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode('utf8')
        print('LOGIN_RESPONSE:', body)
        token = json.loads(body).get('access_token')
except Exception as e:
    print('LOGIN_ERROR:', e)
    raise

if not token:
    print('No token returned')
    raise SystemExit(1)

hdr = {'Authorization': f'Bearer {token}'}
# call bcu cabecalho ativo
try:
    req = urllib.request.Request(base + '/bcu/cabecalho-ativo', headers=hdr)
    with urllib.request.urlopen(req, timeout=30) as resp:
        print('\nBCU_ACTIVE:', resp.read().decode('utf8'))
except Exception as e:
    print('\nBCU_ACTIVE_ERROR:', e)

# call servicos list (request JSON)
try:
    hdr_json = dict(hdr)
    hdr_json['Accept'] = 'application/json'
    req = urllib.request.Request(base + '/servicos?page=1&page_size=5', headers=hdr_json)
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode('utf8')
        ctype = resp.getheader('Content-Type')
        print('\nSERVICOS Content-Type:', ctype)
        print('\nSERVICOS:', body)
except Exception as e:
    print('\nSERVICOS_ERROR:', e)

# fetch openapi and check for servicos path
try:
    req = urllib.request.Request(base + '/openapi.json')
    with urllib.request.urlopen(req, timeout=30) as resp:
        openapi = resp.read().decode('utf8')
        print('\nOpenAPI contains /api/v1/servicos:', '/api/v1/servicos' in openapi)
        print('OpenAPI contains /api/v1/bcu:', '/api/v1/bcu' in openapi)
except Exception as e:
    print('\nOPENAPI_ERROR:', e)
