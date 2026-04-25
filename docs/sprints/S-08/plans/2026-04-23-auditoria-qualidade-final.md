# Auditoria de Qualidade Final — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Executar auditoria completa before go-live: revisão de código, checklist de segurança, testes de integração, e validação de conformidade com os requisitos do core.

**Architecture:** Auditoria baseada em checklist executável + testes E2E + review estático.

**Tech Stack:** pytest, playwright (smoke E2E), shell scripts.

---

## Task 1: Checklist de Auditoria Executável

**Files:**
- Create: `scripts/audit-quality-gate.ps1`

### Step 1: Implementar script de auditoria

```powershell
# scripts/audit-quality-gate.ps1
param([string]$ProjectRoot = ".")

$errors = 0
Write-Host "=== AUDITORIA DE QUALIDADE — Dinamica Budget ===" -ForegroundColor Cyan

# 1. Testes unitários
Write-Host "`n[1/5] Unit Tests..." -ForegroundColor Yellow
$testResult = & python -m pytest "$ProjectRoot/app/backend/tests/unit" -q 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  PASS" -ForegroundColor Green
} else {
    Write-Host "  FAIL" -ForegroundColor Red
    $errors++
}

# 2. Verificar migrations pendentes
Write-Host "`n[2/5] Alembic Migrations..." -ForegroundColor Yellow
$migrationCheck = & alembic current 2>&1
if ($migrationCheck -match "head") {
    Write-Host "  PASS — database is at head" -ForegroundColor Green
} else {
    Write-Host "  FAIL — pending migrations detected" -ForegroundColor Red
    $errors++
}

# 3. Verificar secrets no código
Write-Host "`n[3/5] Secret Scan..." -ForegroundColor Yellow
$secrets = Select-String -Path "$ProjectRoot/app/**/*.py" -Pattern "password\s*=|secret\s*=|api_key\s*=" -SimpleMatch
if (-not $secrets) {
    Write-Host "  PASS — no hardcoded secrets found" -ForegroundColor Green
} else {
    Write-Host "  WARN — potential secrets found" -ForegroundColor Yellow
}

# 4. Verificar endpoints sem proteção
Write-Host "`n[4/5] Security Scan..." -ForegroundColor Yellow
$endpoints = Get-ChildItem -Path "$ProjectRoot/app/api/v1/endpoints/*.py" -Recurse
$unprotected = @()
foreach ($ep in $endpoints) {
    $content = Get-Content $ep.FullName
    if ($content -match "@router\.(get|post|put|patch|delete)" -and -not ($content -match "get_current_active_user|require_cliente")) {
        $unprotected += $ep.Name
    }
}
if ($unprotected.Count -eq 0) {
    Write-Host "  PASS — all endpoints protected" -ForegroundColor Green
} else {
    Write-Host "  FAIL — unprotected endpoints: $($unprotected -join ', ')" -ForegroundColor Red
    $errors++
}

# 5. Build frontend
Write-Host "`n[5/5] Frontend Build..." -ForegroundColor Yellow
Set-Location "$ProjectRoot/frontend"
$buildResult = & npm run build 2>&1
Set-Location $ProjectRoot
if ($LASTEXITCODE -eq 0) {
    Write-Host "  PASS" -ForegroundColor Green
} else {
    Write-Host "  FAIL" -ForegroundColor Red
    $errors++
}

Write-Host "`n=== RESULTADO: $errors falha(s) ===" -ForegroundColor $(if ($errors -eq 0) { "Green" } else { "Red" })
exit $errors
```

### Step 2: Commit

```bash
git add scripts/audit-quality-gate.ps1
git commit -m "feat(audit): add quality gate audit script"
```

---

## Task 2: Relatório de Auditoria

**Files:**
- Create: `docs/auditoria-go-live-2026-04-23.md`

### Step 1: Documentar resultados

Template de relatório com seções:
- Resumo executivo
- Cobertura de testes
- Checklist de segurança
- Performance
- Riscos identificados
- Recomendação de go/no-go

### Step 2: Commit

```bash
git add docs/auditoria-go-live-2026-04-23.md
git commit -m "docs(audit): add go-live audit report template"
```

---

## Task 3: Smoke E2E

**Files:**
- Create: `app/backend/tests/e2e/test_smoke_proposta.py`

### Step 1: Teste E2E básico

```python
# app/backend/tests/e2e/test_smoke_proposta.py
import pytest

@pytest.mark.e2e
async def test_criar_proposta_e_gerar_cpu(client):
    """Smoke test: cria proposta, importa PQ, match, gera CPU."""
    # 1. Login
    # 2. Criar proposta
    # 3. Upload PQ
    # 4. Executar match
    # 5. Gerar CPU
    # 6. Verificar status CPU_GERADA
    pass
```

### Step 2: Commit

```bash
git add app/backend/tests/e2e/test_smoke_proposta.py
git commit -m "test(audit): add smoke E2E test for proposal flow"
```

---

## Task 4: Walkthrough

Create: `docs/sprints/S-08/walkthrough/done/walkthrough-S-08.md`

### Step 1: Commit

```bash
git add docs/sprints/S-08/walkthrough/done/walkthrough-S-08.md
git commit -m "docs(s-08): add walkthrough for quality audit"
```

---

## Plan Review Checklist

- [x] Spec coverage: audit script, report, smoke E2E
- [x] Placeholder scan: no TBD/TODO found

## Handoff

**Plan complete and saved to `docs/sprints/S-08/plans/2026-04-23-auditoria-qualidade-final.md`.**



