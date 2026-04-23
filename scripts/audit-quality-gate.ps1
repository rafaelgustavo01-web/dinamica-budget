param(
    [string]$ProjectRoot = "."
)

$ErrorActionPreference = "Continue"
$resolvedRoot = (Resolve-Path $ProjectRoot).Path
$errors = 0

function Run-Check {
    param(
        [string]$Title,
        [scriptblock]$Action
    )

    Write-Host ""
    Write-Host $Title -ForegroundColor Yellow
    & $Action
    if ($LASTEXITCODE -ne 0) {
        $script:errors++
    }
}

Push-Location $resolvedRoot
try {
    Write-Host "=== AUDITORIA DE QUALIDADE - Dinamica Budget ===" -ForegroundColor Cyan

    Run-Check "[1/5] Unit Tests" {
        python -m pytest app/tests/unit -q
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  PASS" -ForegroundColor Green
        } else {
            Write-Host "  FAIL" -ForegroundColor Red
        }
    }

    Run-Check "[2/5] Alembic Head" {
        $current = alembic current 2>&1
        if ($LASTEXITCODE -eq 0 -and ($current | Out-String) -match "head") {
            Write-Host "  PASS - database is at head" -ForegroundColor Green
            $global:LASTEXITCODE = 0
        } else {
            Write-Host "  FAIL - database is not at head" -ForegroundColor Red
            $current | ForEach-Object { Write-Host "  $_" }
            $global:LASTEXITCODE = 1
        }
    }

    Run-Check "[3/5] Secret Scan" {
        $matches = @()
        $targets = @("app", "frontend/src")
        foreach ($target in $targets) {
            if (Test-Path $target) {
                $matches += Get-ChildItem -Path $target -Recurse -File | Select-String -Pattern @(
                    "password\s*=\s*[`"']",
                    "secret\s*=\s*[`"']",
                    "api[_-]?key\s*=\s*[`"']",
                    "token\s*=\s*[`"']"
                )
            }
        }

        $filtered = @($matches | Where-Object { $_.Path -notmatch "\\tests?\\" })
        if ($filtered.Count -eq 0) {
            Write-Host "  PASS - no hardcoded secrets found" -ForegroundColor Green
            $global:LASTEXITCODE = 0
        } else {
            Write-Host "  FAIL - potential hardcoded secrets found" -ForegroundColor Red
            $filtered | Select-Object -First 10 | ForEach-Object {
                Write-Host ("  {0}:{1}" -f $_.Path, $_.LineNumber)
            }
            $global:LASTEXITCODE = 1
        }
    }

    Run-Check "[4/5] Write Endpoint Protection" {
        python -m pytest app/tests/unit/test_security_p0.py app/tests/unit/test_security_s04.py -q
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  PASS" -ForegroundColor Green
        } else {
            Write-Host "  FAIL" -ForegroundColor Red
        }
    }

    Run-Check "[5/5] Frontend Build" {
        Push-Location "frontend"
        try {
            npm run build
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  PASS" -ForegroundColor Green
            } else {
                Write-Host "  FAIL" -ForegroundColor Red
            }
        } finally {
            Pop-Location
        }
    }

    Write-Host ""
    if ($errors -eq 0) {
        Write-Host "=== RESULTADO: 0 falhas ===" -ForegroundColor Green
    } else {
        Write-Host ("=== RESULTADO: {0} falha(s) ===" -f $errors) -ForegroundColor Red
    }

    exit $errors
} finally {
    Pop-Location
}
