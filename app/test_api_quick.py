"""
Teste Rápido da API Dinamica Budget — Health Check e Validações Básicas

Execute com: python test_api_quick.py
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_result(test_name: str, passed: bool, details: str = ""):
    status = "✅ PASSOU" if passed else "❌ FALHOU"
    print(f"\n{status} — {test_name}")
    if details:
        print(f"   {details}")

def main():
    print("=" * 70)
    print("TESTES RÁPIDOS DA API — DINAMICA BUDGET")
    print("=" * 70)
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    passed = 0
    failed = 0
    
    # Teste 1: Health Check
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        success = resp.status_code == 200
        print_result(
            "01: Health Check",
            success,
            f"Status: {resp.status_code}" + (f"\n   Response: {resp.json()}" if success else "")
        )
        passed += success
        failed += not success
    except Exception as e:
        print_result("01: Health Check", False, f"Erro: {str(e)}")
        failed += 1
    
    # Teste 2: OpenAPI Docs
    try:
        resp = requests.get(f"{BASE_URL}/docs", timeout=5)
        success = resp.status_code == 200 and "swagger" in resp.text.lower()
        print_result(
            "02: OpenAPI Swagger UI",
            success,
            f"Status: {resp.status_code}, Swagger presente: {success}"
        )
        passed += success
        failed += not success
    except Exception as e:
        print_result("02: OpenAPI Swagger UI", False, f"Erro: {str(e)}")
        failed += 1
    
    # Teste 3: OpenAPI JSON
    try:
        resp = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        success = resp.status_code == 200 and "openapi" in resp.text
        print_result(
            "03: OpenAPI JSON Schema",
            success,
            f"Status: {resp.status_code}, OpenAPI presente: {success}"
        )
        passed += success
        failed += not success
    except Exception as e:
        print_result("03: OpenAPI JSON Schema", False, f"Erro: {str(e)}")
        failed += 1
    
    # Teste 4: Auth Login Endpoint Exists
    try:
        resp = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={"username": "", "password": ""},
            timeout=5
        )
        # Não importa se return 422, o importante é NÃO ser 404
        success = resp.status_code != 404
        print_result(
            "04: Auth Login Endpoint",
            success,
            f"Status: {resp.status_code} (esperado != 404)"
        )
        passed += success
        failed += not success
    except Exception as e:
        print_result("04: Auth Login Endpoint", False, f"Erro: {str(e)}")
        failed += 1
    
    # Teste 5: Busca Endpoint Exists
    try:
        resp = requests.get(
            f"{BASE_URL}/api/v1/servicos/buscar",
            params={"q": "teste"},
            timeout=5
        )
        # Não importa o status (pode ser 401 sem auth), importante é NÃO ser 404
        success = resp.status_code != 404
        print_result(
            "05: Busca Servicos Endpoint",
            success,
            f"Status: {resp.status_code} (esperado != 404)"
        )
        passed += success
        failed += not success
    except Exception as e:
        print_result("05: Busca Servicos Endpoint", False, f"Erro: {str(e)}")
        failed += 1
    
    # Teste 6: 404 para endpoint inexistente
    try:
        resp = requests.get(
            f"{BASE_URL}/api/v1/inexistente",
            timeout=5
        )
        success = resp.status_code == 404
        print_result(
            "06: 404 para Endpoint Inexistente",
            success,
            f"Status: {resp.status_code} (esperado 404)"
        )
        passed += success
        failed += not success
    except Exception as e:
        print_result("06: 404 para Endpoint Inexistente", False, f"Erro: {str(e)}")
        failed += 1
    
    # Teste 7: CORS Headers
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        cors_headers = {k: v for k, v in resp.headers.items() if "access-control" in k.lower()}
        success = len(cors_headers) > 0
        print_result(
            "07: CORS Headers Presentes",
            success,
            f"Headers encontrados: {len(cors_headers)}"
        )
        passed += success
        failed += not success
    except Exception as e:
        print_result("07: CORS Headers Presentes", False, f"Erro: {str(e)}")
        failed += 1
    
    # Teste 8: Response Content-Type
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        content_type = resp.headers.get("content-type", "")
        success = "application/json" in content_type
        print_result(
            "08: Response Content-Type JSON",
            success,
            f"Content-Type: {content_type}"
        )
        passed += success
        failed += not success
    except Exception as e:
        print_result("08: Response Content-Type JSON", False, f"Erro: {str(e)}")
        failed += 1
    
    # Resumo
    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)
    total = passed + failed
    print(f"Total de testes: {total}")
    print(f"✅ Passou: {passed}")
    print(f"❌ Falhou: {failed}")
    pct = (passed / total * 100) if total > 0 else 0
    print(f"Taxa de sucesso: {pct:.0f}%")
    print("=" * 70 + "\n")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())
