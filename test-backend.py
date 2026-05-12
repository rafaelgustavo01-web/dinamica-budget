import urllib.request
import json

url = 'http://localhost:8000/api/v1/propostas'
try:
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=3) as resp:
        data = json.loads(resp.read().decode())
        print('✓ Backend respondendo')
        print(f"✓ Propostas encontradas: {len(data.get('items', []))}")
except Exception as e:
    print(f'✗ Erro: {e}')
