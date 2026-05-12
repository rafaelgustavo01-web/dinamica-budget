#!/usr/bin/env python3
"""
Script de teste para verificar se items manager está funcionando
"""

import httpx
import json

BASE_URL = "http://localhost:8000"

def test_api():
    print("\n" + "="*60)
    print("TESTE DE ITEMS MANAGER")
    print("="*60 + "\n")
    
    # 1. Testar se API de items está respondendo
    print("[1] Testando endpoint GET /propostas/{id}/items")
    # Usar um ID de proposta válida - você pode pegar do screenshot
    proposta_id = "0b1c1358-b453-4d31-ca53-83b7ad2803"  # Do screenshot
    
    try:
        resp = httpx.get(f"{BASE_URL}/api/v1/propostas/{proposta_id}/items", timeout=5)
        print(f"    Status: {resp.status_code}")
        if resp.status_code == 200:
            items = resp.json()
            print(f"    Items: {len(items)} encontrados")
            if items:
                print(f"    Primeiro item: {json.dumps(items[0], indent=2)}")
        elif resp.status_code == 404:
            print(f"    [INFO] Proposta não encontrada (esperado, criar nova)")
        else:
            print(f"    [ERRO] {resp.text[:200]}")
    except Exception as e:
        print(f"    [ERRO] {e}")
    
    # 2. Testar se frontend dist está sendo servido
    print("\n[2] Testando se frontend dist está sendo servido")
    try:
        resp = httpx.get(f"{BASE_URL}/", timeout=5)
        print(f"    Status: {resp.status_code}")
        if "<!DOCTYPE html" in resp.text or "<!doctype html" in resp.text:
            print(f"    ✓ HTML index.html está sendo servido")
            if "ProposalItemsManager" in resp.text or "proposalItemsApi" in resp.text:
                print(f"    ✓ Novo código detectado no HTML")
            else:
                print(f"    ⚠ Novo código NÃO detectado (pode estar nos assets)")
        else:
            print(f"    ⚠ Resposta não é HTML: {resp.text[:200]}")
    except Exception as e:
        print(f"    [ERRO] {e}")
    
    # 3. Testar assets
    print("\n[3] Testando se arquivos assets estão disponíveis")
    try:
        resp = httpx.get(f"{BASE_URL}/assets/", timeout=5)
        print(f"    Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"    ✓ Diretório assets está sendo servido")
    except Exception as e:
        print(f"    [INFO] Assets podem não estar listáveis: {e}")
    
    # 4. Testar rotas do backend
    print("\n[4] Verificando rotas de items no backend")
    try:
        resp = httpx.get(f"{BASE_URL}/api/v1/", timeout=5)
        if resp.status_code in [200, 404]:  # 404 é normal se rota não existe
            print(f"    Backend respondendo na porta 8000")
        else:
            print(f"    Status: {resp.status_code}")
    except Exception as e:
        print(f"    [ERRO] Backend não respondendo: {e}")
    
    print("\n" + "="*60)
    print("TESTE CONCLUÍDO")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_api()
