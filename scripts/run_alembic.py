import sys
sys.path.insert(0, r'C:\DinamicaBudget\venv\Lib\site-packages')
from alembic.config import Config, main
import os
os.chdir(r'C:\DinamicaBudget')
main(argv=sys.argv[1:])
