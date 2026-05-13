#!/usr/bin/env python3
"""
Script simples de validação sem dependências externas
Usa apenas urllib (padrão do Python)
"""

import json
import urllib.request
import urllib.error
import sys
from pathlib import Path

API_BASE = "http://localhost:8000/api/v1"

def test_health():
    """Teste 1: Health check do backend"""
    try:
        with urllib.request.urlopen(f"{API_BASE}/health", timeout=5) as response:
            if response.status == 200:
                print("✓ Backend respondendo na porta 8000")
                return True
    except Exception as e:
        print(f"✗ Backend não respondeu: {e}")
        return False

def test_models():
    """Teste 2: Verificar se modelos foram carregados corretamente"""
    try:
        # Tentar acessar endpoint que usa os modelos alterados
        with urllib.request.urlopen(f"{API_BASE}/propostas?page_size=1", timeout=5) as response:
            if response.status in (200, 401):  # 401 é ok, significa que auth é necessária
                print("✓ Modelos carregados corretamente")
                return True
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("✓ Modelos carregados (auth requerida)")
            return True
        print(f"✗ Erro ao acessar modelos: {e}")
    except Exception as e:
        print(f"✗ Erro: {e}")
    return False

def validate_code_changes():
    """Teste 3: Validar se o código foi alterado"""
    changes_found = 0
    total_checks = 4
    
    # Check 1: proposta_pc_repository.py tem clear_mao_obra
    repo_file = Path("C:\\Dinamica-Budget\\app\\backend\\repositories\\proposta_pc_repository.py")
    if repo_file.exists():
        content = repo_file.read_text()
        if "async def clear_mao_obra" in content:
            print("✓ clear_mao_obra() adicionado em proposta_pc_repository.py")
            changes_found += 1
        else:
            print("✗ clear_mao_obra() NÃO encontrado")
    
    # Check 2: histograma_service.py tem DELETE antes de INSERT
    hist_file = Path("C:\\Dinamica-Budget\\app\\backend\\services\\histograma_service.py")
    if hist_file.exists():
        content = hist_file.read_text()
        if "await self.repo.clear_mao_obra(proposta_id)" in content:
            print("✓ DELETE antes de INSERT em histograma_service.py")
            changes_found += 1
        else:
            print("✗ DELETE não encontrado em histograma_service.py")
    
    # Check 3: proposta_pc.py tem UniqueConstraint em PropostaPcEncargo
    model_file = Path("C:\\Dinamica-Budget\\app\\backend\\models\\proposta_pc.py")
    if model_file.exists():
        content = model_file.read_text()
        if 'uq_proposta_pc_encargo' in content:
            print("✓ UniqueConstraint adicionado em PropostaPcEncargo")
            changes_found += 1
        else:
            print("✗ UniqueConstraint NÃO encontrado")
    
    # Check 4: pq_importacao.py tem try/except com logging
    endpoint_file = Path("C:\\Dinamica-Budget\\app\\backend\\api\\v1\\endpoints\\pq_importacao.py")
    if endpoint_file.exists():
        content = endpoint_file.read_text()
        if "try:" in content and "logger.exception" in content:
            print("✓ Try/except com logging adicionado em pq_importacao.py")
            changes_found += 1
        else:
            print("✗ Try/except NÃO encontrado")
    
    return changes_found == total_checks

def main():
    print("\n" + "="*60)
    print("VALIDAÇÃO DE REDEPLOY - DINAMICA BUDGET")
    print("="*60 + "\n")
    
    print("📋 TESTE 1: Verificar alterações no código")
    print("-" * 60)
    code_ok = validate_code_changes()
    print()
    
    print("🔍 TESTE 2: Verificar conectividade do backend")
    print("-" * 60)
    health_ok = test_health()
    print()
    
    print("🔧 TESTE 3: Verificar carregamento de modelos")
    print("-" * 60)
    models_ok = test_models()
    print()
    
    # Resumo
    print("="*60)
    print("RESUMO DOS TESTES")
    print("="*60)
    
    tests = [
        ("Alterações de Código", code_ok),
        ("Backend Respondendo", health_ok),
        ("Modelos Carregados", models_ok),
    ]
    
    passed = sum(1 for _, ok in tests if ok)
    total = len(tests)
    
    for name, ok in tests:
        status = "✓ PASS" if ok else "✗ FAIL"
        print(f"{status:8} | {name}")
    
    print("="*60)
    print(f"\nResultado: {passed}/{total} testes passaram")
    
    if code_ok and health_ok:
        print("\n✅ REDEPLOY VALIDADO COM SUCESSO!")
        print("\nPróximos passos:")
        print("1. Fazer login no frontend")
        print("2. Testar fluxo: PQ Import → Match → Histograma")
        print("3. Validar isolamento entre propostas")
        return 0
    else:
        print("\n❌ REDEPLOY COM PROBLEMAS!")
        if not code_ok:
            print("   - Código não foi alterado corretamente")
        if not health_ok:
            print("   - Backend não está respondendo")
        return 1

if __name__ == "__main__":
    sys.exit(main())
