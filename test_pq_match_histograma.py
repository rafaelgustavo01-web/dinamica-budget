#!/usr/bin/env python3
"""
Script para validar fluxo de PQ → Match → Histograma

Uso:
  python test_pq_match_histograma.py
  
Pré-requisitos:
  - Backend rodando em http://localhost:8000
  - Ter credenciais de login válidas
  - Ter um cliente e pelo menos 2 propostas
"""

import asyncio
import httpx
import json
from pathlib import Path
from uuid import UUID

# Configuração
API_BASE = "http://localhost:8000/api/v1"
TIMEOUT = 30

# Cores para output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_ok(msg: str):
    print(f"{GREEN}✓ {msg}{RESET}")


def print_error(msg: str):
    print(f"{RED}✗ {msg}{RESET}")


def print_info(msg: str):
    print(f"{BLUE}ℹ {msg}{RESET}")


def print_warning(msg: str):
    print(f"{YELLOW}⚠ {msg}{RESET}")


async def login(email: str, password: str) -> str | None:
    """Faz login e retorna o token"""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.post(
                f"{API_BASE}/auth/login",
                json={"email": email, "password": password}
            )
            if resp.status_code == 200:
                token = resp.json().get("access_token")
                print_ok(f"Login com sucesso: {email}")
                return token
            else:
                print_error(f"Falha no login: {resp.status_code} - {resp.text}")
                return None
        except Exception as exc:
            print_error(f"Erro ao fazer login: {exc}")
            return None


async def get_propostas(token: str, cliente_id: UUID | str) -> list[dict]:
    """Lista propostas de um cliente"""
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=headers) as client:
        try:
            resp = await client.get(
                f"{API_BASE}/propostas",
                params={"cliente_id": str(cliente_id), "page_size": 50}
            )
            if resp.status_code == 200:
                propostas = resp.json().get("items", [])
                print_ok(f"Encontradas {len(propostas)} proposta(s)")
                return propostas
            else:
                print_error(f"Erro ao listar propostas: {resp.status_code}")
                return []
        except Exception as exc:
            print_error(f"Erro ao listar propostas: {exc}")
            return []


async def upload_pq(token: str, proposta_id: str, arquivo: str) -> bool:
    """Faz upload do arquivo PQ"""
    headers = {"Authorization": f"Bearer {token}"}
    with open(arquivo, "rb") as f:
        files = {"arquivo": (Path(arquivo).name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        async with httpx.AsyncClient(timeout=60, headers=headers) as client:
            try:
                resp = await client.post(
                    f"{API_BASE}/propostas/{proposta_id}/pq/importar",
                    files=files
                )
                if resp.status_code == 201:
                    print_ok(f"Upload de PQ concluído")
                    return True
                else:
                    print_error(f"Erro ao fazer upload: {resp.status_code} - {resp.text}")
                    return False
            except Exception as exc:
                print_error(f"Erro ao fazer upload: {exc}")
                return False


async def executar_match(token: str, proposta_id: str) -> dict | None:
    """Executa match de itens"""
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=60, headers=headers) as client:
        try:
            resp = await client.post(
                f"{API_BASE}/propostas/{proposta_id}/pq/match"
            )
            if resp.status_code == 200:
                resultado = resp.json()
                print_ok(f"Match executado: {resultado['processados']} processados, {resultado['sugeridos']} sugeridos, {resultado['sem_match']} sem match")
                return resultado
            else:
                print_error(f"Erro ao executar match: {resp.status_code}")
                if resp.status_code == 502:
                    print_warning("Erro 502 - verifique logs do backend")
                print_info(f"Response: {resp.text[:200]}")
                return None
        except Exception as exc:
            print_error(f"Erro ao executar match: {exc}")
            return None


async def montar_histograma(token: str, proposta_id: str) -> dict | None:
    """Monta o histograma"""
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=60, headers=headers) as client:
        try:
            resp = await client.post(
                f"{API_BASE}/propostas/{proposta_id}/montar-histograma"
            )
            if resp.status_code == 200:
                resultado = resp.json()
                print_ok(f"Histograma montado: {resultado}")
                return resultado
            else:
                print_error(f"Erro ao montar histograma: {resp.status_code}")
                return None
        except Exception as exc:
            print_error(f"Erro ao montar histograma: {exc}")
            return None


async def get_histograma(token: str, proposta_id: str) -> dict | None:
    """Obtém o histograma"""
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        try:
            resp = await client.get(
                f"{API_BASE}/propostas/{proposta_id}/histograma"
            )
            if resp.status_code == 200:
                data = resp.json()
                mo_count = len(data.get("mao_obra", []))
                eqp_count = len(data.get("equipamentos", []))
                epi_count = len(data.get("epis", []))
                fer_count = len(data.get("ferramentas", []))
                print_ok(f"Histograma: MO={mo_count}, EQP={eqp_count}, EPI={epi_count}, FER={fer_count}")
                return data
            else:
                print_error(f"Erro ao obter histograma: {resp.status_code}")
                return None
        except Exception as exc:
            print_error(f"Erro ao obter histograma: {exc}")
            return None


async def main():
    print(f"{BLUE}=== Validação do Fluxo PQ + Match + Histograma ==={RESET}\n")
    
    # Configuração manual (ajuste conforme necessário)
    print(f"{YELLOW}Configuração:{RESET}")
    email = input("Email: ").strip()
    password = input("Senha: ").strip()
    cliente_id = input("ID do Cliente (UUID): ").strip()
    arquivo_pq = input("Caminho do arquivo PQ.xlsx: ").strip() or "PQ.xlsx"
    
    if not Path(arquivo_pq).exists():
        print_error(f"Arquivo {arquivo_pq} não encontrado")
        return
    
    print()
    
    # 1. Login
    token = await login(email, password)
    if not token:
        return
    print()
    
    # 2. Listar propostas
    propostas = await get_propostas(token, cliente_id)
    if len(propostas) < 2:
        print_warning(f"Precisa de pelo menos 2 propostas (encontradas {len(propostas)})")
        if len(propostas) == 0:
            return
    print()
    
    prop_a = propostas[0]
    prop_b = propostas[1] if len(propostas) > 1 else None
    
    print(f"{BLUE}Proposta A (para testar): {prop_a['id']}{RESET}")
    if prop_b:
        print(f"{BLUE}Proposta B (para verificar isolamento): {prop_b['id']}{RESET}")
    print()
    
    # 3. Upload PQ em Proposta A
    print(f"{BLUE}--- Teste 1: Upload de PQ ---{RESET}")
    if not await upload_pq(token, prop_a["id"], arquivo_pq):
        return
    print()
    
    # 4. Executar Match
    print(f"{BLUE}--- Teste 2: Executar Match ---{RESET}")
    match_result = await executar_match(token, prop_a["id"])
    if not match_result:
        return
    print()
    
    # 5. Montar Histograma (Proposta A)
    print(f"{BLUE}--- Teste 3: Montar Histograma (Proposta A) ---{RESET}")
    hist_a_1 = await montar_histograma(token, prop_a["id"])
    if not hist_a_1:
        return
    print()
    
    # 6. Verificar Histograma (Proposta A)
    print(f"{BLUE}--- Teste 4: Verificar Histograma (Proposta A) ---{RESET}")
    data_a_1 = await get_histograma(token, prop_a["id"])
    print()
    
    # 7. Verificar Histograma (Proposta B) - deve estar vazio
    if prop_b:
        print(f"{BLUE}--- Teste 5: Verificar Isolamento (Proposta B deve estar vazia) ---{RESET}")
        data_b_1 = await get_histograma(token, prop_b["id"])
        
        if data_b_1:
            mo_b = len(data_b_1.get("mao_obra", []))
            if mo_b > 0:
                print_error(f"FALHA: Proposta B tem {mo_b} itens de MO (deveria estar vazia!)")
            else:
                print_ok("SUCESSO: Proposta B está isolada (vazia)")
        print()
    
    # 8. Regenerar Histograma (Proposta A) - verificar duplicatas
    print(f"{BLUE}--- Teste 6: Regenerar Histograma (verificar sem duplicatas) ---{RESET}")
    hist_a_2 = await montar_histograma(token, prop_a["id"])
    if hist_a_2 and hist_a_1:
        for chave in ["mao_obra", "equipamentos", "epis", "ferramentas"]:
            cnt_1 = hist_a_1.get(chave, 0)
            cnt_2 = hist_a_2.get(chave, 0)
            if cnt_1 == cnt_2:
                print_ok(f"{chave}: {cnt_1} == {cnt_2} (sem duplicatas)")
            else:
                print_error(f"{chave}: {cnt_1} != {cnt_2} (pode haver duplicatas)")
    print()
    
    print(f"{GREEN}=== Testes Concluídos ==={RESET}")


if __name__ == "__main__":
    asyncio.run(main())
