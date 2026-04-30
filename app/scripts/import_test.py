import sys
from pathlib import Path
import importlib, traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    importlib.import_module('backend.api.v1.endpoints.servicos')
    print('IMPORT_OK')
except Exception:
    traceback.print_exc()
