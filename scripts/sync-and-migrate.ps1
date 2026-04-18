$src = "C:\Dinamica-Budget"
$dst = "C:\DinamicaBudget"

# Migrations
$migrations = @(
    "012_base_consulta_pc_orcamento.py",
    "013_expand_pc_numeric_ranges.py",
    "014_expand_pc_encargo_text_lengths.py",
    "015_expand_pc_mao_obra_beneficios.py"
)
foreach ($m in $migrations) {
    Copy-Item "$src\alembic\versions\$m" "$dst\alembic\versions\$m" -Force
}

# Models
Copy-Item "$src\app\models\pc_tabelas.py" "$dst\app\models\pc_tabelas.py" -Force
Copy-Item "$src\app\models\__init__.py" "$dst\app\models\__init__.py" -Force

# Schemas
Copy-Item "$src\app\schemas\pc_tabelas.py" "$dst\app\schemas\pc_tabelas.py" -Force

# Services
Copy-Item "$src\app\services\pc_tabelas_service.py" "$dst\app\services\pc_tabelas_service.py" -Force

# Endpoints
Copy-Item "$src\app\api\v1\endpoints\pc_tabelas.py" "$dst\app\api\v1\endpoints\pc_tabelas.py" -Force
Copy-Item "$src\app\api\v1\router.py" "$dst\app\api\v1\router.py" -Force

Write-Host "=== ALL FILES COPIED ==="

# Run migrations
Write-Host "Running migrations..."
Set-Location $dst
$result = & "$dst\venv\Scripts\alembic.exe" upgrade head 2>&1
$result | Out-String | Write-Host

Write-Host "=== MIGRATION DONE ==="
