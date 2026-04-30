import sys
from pathlib import Path
proj = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(proj))
from backend.main import app
import json

routes = []
for r in app.routes:
    routes.append({'path': getattr(r, 'path', str(r)), 'methods': list(getattr(r, 'methods', [])), 'name': getattr(r, 'name', '')})

print(json.dumps(routes, indent=2, ensure_ascii=False))
