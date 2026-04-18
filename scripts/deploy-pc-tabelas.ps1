param([string]$LogFile = "C:\Dinamica-Budget\logs\deploy-pc-tabelas.log")

$src = "C:\Dinamica-Budget"
$dst = "C:\DinamicaBudget"
$out = @()
$out += "=== DEPLOY PC TABELAS START ==="
$out += (Get-Date).ToString()

# 1. Copy migrations
$out += "[1] Copying migrations"
$migrations = @(
    "012_base_consulta_pc_orcamento.py",
    "013_expand_pc_numeric_ranges.py",
    "014_expand_pc_encargo_text_lengths.py",
    "015_expand_pc_mao_obra_beneficios.py"
)
foreach ($m in $migrations) {
    try {
        Copy-Item "$src\alembic\versions\$m" "$dst\alembic\versions\$m" -Force
        $out += "  OK: $m"
    } catch {
        $out += "  WARN: $m - $_"
    }
}

# 2. Copy Python files
$out += "[2] Copying Python files"
$files = @(
    @{ S="$src\app\models\pc_tabelas.py"; D="$dst\app\models\pc_tabelas.py" },
    @{ S="$src\app\models\__init__.py"; D="$dst\app\models\__init__.py" },
    @{ S="$src\app\schemas\pc_tabelas.py"; D="$dst\app\schemas\pc_tabelas.py" },
    @{ S="$src\app\services\pc_tabelas_service.py"; D="$dst\app\services\pc_tabelas_service.py" },
    @{ S="$src\app\api\v1\endpoints\pc_tabelas.py"; D="$dst\app\api\v1\endpoints\pc_tabelas.py" },
    @{ S="$src\app\api\v1\router.py"; D="$dst\app\api\v1\router.py" }
)
foreach ($f in $files) {
    try {
        Copy-Item $f.S $f.D -Force
        $out += "  OK: $($f.D | Split-Path -Leaf)"
    } catch {
        $out += "  FAIL: $($f.D | Split-Path -Leaf) - $_"
    }
}

# 3. Run migrations
$out += "[3] Running Alembic migrations"
try {
    Push-Location $dst
    $migResult = & "$dst\venv\Scripts\alembic.exe" upgrade head 2>&1
    $out += $migResult
    $out += "  Migrations complete"
    Pop-Location
} catch {
    $out += "  FAIL migrations: $_"
}

# 4. Seed PC Tabelas data from Excel
$out += "[4] Seeding PC Tabelas from Excel"
$seedScript = @"
import sys, os, asyncio
sys.path.insert(0, r'$dst')
os.chdir(r'$dst')

from dotenv import load_dotenv
load_dotenv(r'$dst\.env')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.pc_tabelas_service import importar_pc_tabelas
import asyncio

async def seed():
    db_url = os.environ.get('DATABASE_URL')
    engine = create_async_engine(db_url, echo=False)
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    xlsx_path = r'C:\Dinamica-Budget\tabelas\PC tabelas.xlsx'
    with open(xlsx_path, 'rb') as f:
        data = f.read()
    async with SessionLocal() as session:
        cab = await importar_pc_tabelas(session, data, 'PC tabelas.xlsx')
        print(f'Seeded: {cab.id} - {cab.nome_arquivo}')
    await engine.dispose()

asyncio.run(seed())
"@
$seedFile = "$env:TEMP\seed_pc.py"
$seedScript | Set-Content $seedFile -Encoding UTF8
try {
    $seedResult = & "$dst\venv\Scripts\python.exe" $seedFile 2>&1
    $out += $seedResult
    $out += "  Seed complete"
} catch {
    $out += "  FAIL seed: $_"
}

# 5. Restart API service
$out += "[5] Restarting API service"
try {
    nssm restart DinamicaBudgetAPI 2>&1 | Out-Null
    $out += "  API restarted"
} catch {
    $out += "  WARN restart: $_"
}

$out += "=== DONE ==="
$out | Set-Content $LogFile -Encoding UTF8
Write-Host ($out -join "`n")
