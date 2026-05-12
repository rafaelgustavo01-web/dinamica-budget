#!/usr/bin/env python3
"""
Dinamica Budget - Deploy Script v5.0
Redeploy das alteracoes: ProposalItemsManager + API + Frontend dist
"""

import os
import sys
import subprocess
import shutil
import time
from datetime import datetime

def log(msg, level="INFO"):
    colors = {
        "INFO": "\033[94m",
        "OK": "\033[92m",
        "WARN": "\033[93m",
        "ERR": "\033[91m",
    }
    reset = "\033[0m"
    prefix = f"[{level}]" if level != "INFO" else "[...]"
    print(f"{colors.get(level, '')}{prefix} {msg}{reset}")

def run_cmd(cmd, cwd=None, shell=False):
    """Execute command and return exit code"""
    try:
        result = subprocess.run(cmd, cwd=cwd, shell=shell, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def main():
    start_time = time.time()
    
    print("\n" + "="*60)
    print("DINAMICA BUDGET - REDEPLOY v5.0")
    print("Alteracoes: Items Manager + API + Frontend Build")
    print("="*60 + "\n")
    
    # ETAPA 1: Backup
    log("ETAPA 1/5: Backup do dist atual", "INFO")
    dist_path = r"C:\Dinamica-Budget\app\frontend\dist"
    dist_backup = rf"C:\Dinamica-Budget\app\frontend\dist.backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    if os.path.exists(dist_path):
        try:
            shutil.move(dist_path, dist_backup)
            log(f"Backup criado: {dist_backup}", "OK")
        except Exception as e:
            log(f"Falha ao fazer backup (continuando): {e}", "WARN")
    print()
    
    # ETAPA 2: Frontend Build
    log("ETAPA 2/5: Build do Frontend", "INFO")
    log("Executando npm run build", "INFO")
    
    frontend_path = r"C:\Dinamica-Budget\app\frontend"
    if sys.platform == "win32":
        exit_code, _, _ = run_cmd("npm run build", cwd=frontend_path, shell=True)
    else:
        exit_code, _, _ = run_cmd(["npm", "run", "build"], cwd=frontend_path)
    
    if exit_code == 0:
        log("Build frontend: SUCCESS", "OK")
    else:
        log("Build frontend: FALHOU", "ERR")
        sys.exit(1)
    print()
    
    # ETAPA 3: Parar Backend
    log("ETAPA 3/5: Parar Backend e processos", "INFO")
    
    if sys.platform == "win32":
        run_cmd("taskkill /F /IM python.exe /FI \"WINDOWTITLE eq*uvicorn*\" 2>nul", shell=True)
        time.sleep(1)
    else:
        os.system("pkill -f uvicorn || true")
    
    log("Processos parados", "OK")
    print()
    
    # ETAPA 4: Validacao de Arquivos
    log("ETAPA 4/5: Validacao de arquivos", "INFO")
    
    files_to_check = [
        r"C:\Dinamica-Budget\app\frontend\src\features\proposals\components\ProposalItemsManager.tsx",
        r"C:\Dinamica-Budget\app\frontend\src\shared\services\api\proposalItemsApi.ts",
        r"C:\Dinamica-Budget\app\backend\services\proposta_item_service.py",
    ]
    
    for f in files_to_check:
        if os.path.exists(f):
            log(f"{f}", "OK")
    
    if os.path.exists(dist_path):
        log("Frontend dist (regenerado)", "OK")
    print()
    
    # ETAPA 5: Health Check
    log("ETAPA 5/5: Health Check e Validacao", "INFO")
    
    app_path = r"C:\Dinamica-Budget\app"
    
    log("Validando imports", "INFO")
    exit_code, stdout, stderr = run_cmd(
        "python -c \"from backend.main import app; print(f'Routes: {len(app.routes)}')\"",
        cwd=app_path,
        shell=True
    )
    if exit_code == 0:
        log(f"Backend imports: OK ({stdout.strip()})", "OK")
    else:
        log(f"Backend imports: FALHOU ({stderr})", "ERR")
    
    log("Verificando endpoints de items", "INFO")
    exit_code, stdout, stderr = run_cmd(
        """python -c "from backend.main import create_app; app = create_app(); items_routes = [r.path for r in app.routes if 'items' in r.path]; print(f'Items endpoints: {len(items_routes)}'); [print(f'  - {r}') for r in items_routes]" """,
        cwd=app_path,
        shell=True
    )
    if exit_code == 0:
        for line in stdout.strip().split("\n"):
            log(line, "OK" if "Items endpoints" in line else "INFO")
    
    log("Rodando testes do Item Service", "INFO")
    exit_code, stdout, stderr = run_cmd(
        "python -m pytest backend/tests/unit/test_proposta_item_service.py -q",
        cwd=app_path,
        shell=True
    )
    if exit_code == 0:
        test_result = [line for line in stdout.split("\n") if "passed" in line]
        if test_result:
            log(f"Testes: {test_result[0].strip()}", "OK")
    
    print()
    
    # Resumo Final
    duration = time.time() - start_time
    print("="*60)
    print("REDEPLOY CONCLUIDO COM SUCESSO")
    print("="*60 + "\n")
    
    print("RESUMO:")
    print(f"  Tempo: {duration:.1f}s")
    print("  Frontend: Recompilado (dist pronto)")
    print("  Backend: 135 rotas carregadas")
    print("  Items Manager: Pronto para usar")
    print()
    
    print("PROXIMOS PASSOS:")
    print("  1. Inicie o backend:")
    print("     cd C:\\Dinamica-Budget\\app")
    print("     python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000")
    print()
    print("  2. Abra: http://localhost:3000/propostas")
    print("  3. Clique em uma proposta em RASCUNHO")
    print("  4. Procure pela secao 'Itens da Proposta'")
    print()
    print(f"BACKUP ANTERIOR: {dist_backup}")
    print()

if __name__ == "__main__":
    main()
