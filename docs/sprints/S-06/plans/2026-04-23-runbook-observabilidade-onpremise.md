# Observabilidade e Operação On-Premise — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar runbook operacional, health checks e scripts de diagnóstico para operação on-premise do Dinamica Budget.

**Architecture:** Scripts PowerShell + endpoints de health check FastAPI. Sem dependência de cloud.

**Tech Stack:** PowerShell, FastAPI, PostgreSQL, pytest.

---

## Task 1: Health Check Endpoint

**Files:**
- Create: `app/api/v1/endpoints/health.py`
- Modify: `app/api/v1/router.py`

### Step 1: Implementar endpoint de saúde

```python
# app/api/v1/endpoints/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db_session

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check(db: AsyncSession = Depends(get_db_session)):
    """Retorna status da aplicação e conexão com banco."""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": "2.0.0",
    }
```

### Step 2: Commit

```bash
git add app/api/v1/endpoints/health.py
git commit -m "feat(obs): add health check endpoint"
```

---

## Task 2: Script de Diagnóstico On-Premise

**Files:**
- Create: `scripts/health-check.ps1`

### Step 1: Implementar script

```powershell
# scripts/health-check.ps1
param(
    [string]$ApiUrl = "http://localhost:8000",
    [string]$DbHost = "localhost",
    [int]$DbPort = 5432
)

Write-Host "=== Dinamica Budget — Health Check ===" -ForegroundColor Cyan

# Testar API
Write-Host "`n[1/3] API Health..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$ApiUrl/api/v1/health/" -TimeoutSec 10
    if ($response.status -eq "healthy") {
        Write-Host "  API: OK" -ForegroundColor Green
    } else {
        Write-Host "  API: DEGRADED ($($response.database))" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  API: FAIL — $_" -ForegroundColor Red
}

# Testar PostgreSQL
Write-Host "`n[2/3] PostgreSQL Connection..." -ForegroundColor Yellow
try {
    $pgResult = & psql -h $DbHost -p $DbPort -U postgres -c "SELECT version();" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  PostgreSQL: OK" -ForegroundColor Green
    } else {
        Write-Host "  PostgreSQL: FAIL" -ForegroundColor Red
    }
} catch {
    Write-Host "  PostgreSQL: NOT INSTALLED or UNREACHABLE" -ForegroundColor Red
}

# Testar disco
Write-Host "`n[3/3] Disk Space..." -ForegroundColor Yellow
$disk = Get-WmiObject -Class Win32_LogicalDisk | Where-Object { $_.DeviceID -eq "C:" }
$freePercent = [math]::Round(($disk.FreeSpace / $disk.Size) * 100, 1)
if ($freePercent -gt 10) {
    Write-Host "  Disk: OK ($freePercent% free)" -ForegroundColor Green
} else {
    Write-Host "  Disk: LOW ($freePercent% free)" -ForegroundColor Red
}

Write-Host "`n=== End of Health Check ===" -ForegroundColor Cyan
```

### Step 2: Commit

```bash
git add scripts/health-check.ps1
git commit -m "feat(obs): add on-premise health check script"
```

---

## Task 3: Runbook Operacional

**Files:**
- Create: `docs/runbook-operacional.md`

### Step 1: Documentar operações

```markdown
# Runbook Operacional — Dinamica Budget

## Instalação On-Premise

1. Pré-requisitos: PostgreSQL 15+, Python 3.12, Node.js 20
2. Clone do repositório
3. Configurar `.env` com credenciais do banco
4. Executar Alembic: `alembic upgrade head`
5. Iniciar backend: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
6. Iniciar frontend: `cd frontend && npm run build && serve -s dist`

## Operações Diárias

- Health check: `powershell -File scripts/health-check.ps1`
- Backup banco: `pg_dump -Fc dinamica_budget > backup_$(date +%Y%m%d).dump`
- Ver logs: `tail -f logs/app.log`

## Troubleshooting

| Sintoma | Causa provável | Ação |
|---------|---------------|------|
| API retorna 500 | Conexão com banco perdida | Verificar PostgreSQL; reiniciar app |
| Busca lenta | Índices GIN desatualizados | Reindexar: `REINDEX INDEX CONCURRENTLY ix_base_tcpo_descricao_gin` |
| Upload Excel falha | Encoding incorreto | Converter para UTF-8 antes do upload |
```

### Step 2: Commit

```bash
git add docs/runbook-operacional.md
git commit -m "docs(obs): add operational runbook"
```

---

## Task 4: Testes e Walkthrough

### Step 1: Testar health endpoint

```bash
pytest app/backend/tests/unit/test_health.py -v
```

### Step 2: Walkthrough

Create: `docs/sprints/S-06/walkthrough/done/walkthrough-S-06.md`

### Step 3: Commit

```bash
git add docs/sprints/S-06/walkthrough/done/walkthrough-S-06.md
git commit -m "docs(s-06): add walkthrough for observability"
```

---

## Plan Review Checklist

- [x] Spec coverage: health endpoint, diagnostic script, runbook
- [x] Placeholder scan: no TBD/TODO found
- [x] On-premise friendly: sem dependências cloud

## Handoff

**Plan complete and saved to `docs/sprints/S-07/plans/2026-04-23-runbook-observabilidade-onpremise.md`.**



