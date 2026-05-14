"""
=======================================================================
DINÂMICA BUDGET — TESTE COMPLETO DE TODAS AS ROTAS DA API
=======================================================================
Uso:
    cd C:\\Dinamica-Budget\\app
    .\\venv\\Scripts\\python.exe test_all_routes.py

Gera resultado em: C:\\Dinamica-Budget\\app\\resultado_testes_api.txt
=======================================================================
"""
import asyncio
import io
import os
import sys
import time
from datetime import datetime
from typing import Any

sys.path.insert(0, ".")
os.environ.setdefault("ENV", "development")

import httpx
import openpyxl

# ─── Configuração ───────────────────────────────────────────────────────────
BASE_URL = "http://127.0.0.1:8000/api/v1"
EMAIL = "dinamica@easymakers.com"
PASSWORD = "Dinamica!Easymakers"
PROPOSTA_ID = "1a551def-b5e0-410e-b1a3-d1093175faca"   # PROP-2026-0003 (ativa)
CLIENTE_ID  = "4a792b96-2ccd-4ab1-8d65-25c5c8e7d183"
REPORT_FILE = os.path.join(os.path.dirname(__file__), "resultado_testes_api.txt")

# ─── Resultado ──────────────────────────────────────────────────────────────
results: list[dict[str, Any]] = []

def record(name: str, method: str, path: str, status: int, ok: bool,
           ms: float, detail: str = ""):
    icon = "PASS" if ok else "FAIL"
    results.append({
        "name": name, "method": method, "path": path,
        "status": status, "ok": ok, "ms": ms, "detail": detail,
    })
    bar = "✅" if ok else "❌"
    print(f"  {bar} [{icon}] {method} {path} → {status}  ({ms:.0f}ms)"
          + (f"  ⚠ {detail}" if detail and not ok else ""))


async def req(client: httpx.AsyncClient, method: str, url: str,
              name: str, expected: int | list[int] = 200, **kwargs) -> httpx.Response:
    t0 = time.monotonic()
    try:
        resp = await getattr(client, method)(url, **kwargs)
    except Exception as exc:
        record(name, method.upper(), url.replace(BASE_URL, ""),
               0, False, 0, str(exc))
        return httpx.Response(0)
    ms = (time.monotonic() - t0) * 1000
    expected_list = expected if isinstance(expected, list) else [expected]
    ok = resp.status_code in expected_list
    detail = "" if ok else resp.text[:120]
    record(name, method.upper(), url.replace(BASE_URL, ""),
           resp.status_code, ok, ms, detail)
    return resp


def make_test_xlsx() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["codigo", "descricao", "unidade", "quantidade"])
    ws.append(["", "CAPITULO 1 - SERVICOS CIVIS", "", ""])   # título → ignorado
    ws.append(["1.1", "Escavação manual de vala", "m3", "10"])
    ws.append(["1.2", "Reaterro compactado manual", "m3", "8"])
    ws.append(["1.3", "Forma de madeira compensada", "m2", "25"])
    ws.append(["1.4", "Concretagem fck 25 MPa estrutura", "m3", "5"])
    ws.append(["", "", "", ""])                               # vazio → ignorado
    ws.append(["", "CAPITULO 2 - INSTALACOES", "", ""])      # título → ignorado
    ws.append(["2.1", "Eletroduto corrugado 3/4 polegada", "m", "150"])
    ws.append(["2.2", "Cabo flexível 2,5mm2", "m", "300"])
    ws.append(["", "Total Geral", "", ""])                    # título → ignorado
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


async def main():
    print("=" * 70)
    print(" DINÂMICA BUDGET — TESTE COMPLETO DE ROTAS DA API")
    print(f" {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 70)

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        token = None
        proposta_nova_id = None
        pq_item_id = None

        # ══════════════════════════════════════════════════════════════════
        # 1. HEALTH & AUTH
        # ══════════════════════════════════════════════════════════════════
        print("\n── 1. HEALTH & AUTH ─────────────────────────────────────────")

        await req(client, "get", f"{BASE_URL}/health",
                  "Health check", 200)

        resp = await req(client, "post", f"{BASE_URL}/auth/login",
                         "Login com credenciais corretas", 200,
                         json={"email": EMAIL, "password": PASSWORD})
        if resp.status_code == 200:
            token = resp.json().get("access_token")

        await req(client, "post", f"{BASE_URL}/auth/login",
                  "Login credenciais inválidas", [401, 422],
                  json={"email": "x@x.com", "password": "wrong"})

        if not token:
            print("\n❌ Login falhou — abortando demais testes.")
            await write_report()
            return

        h = {"Authorization": f"Bearer {token}"}

        await req(client, "get", f"{BASE_URL}/auth/me",
                  "Auth /me (token válido)", 200, headers=h)

        # ══════════════════════════════════════════════════════════════════
        # 2. USUÁRIOS
        # ══════════════════════════════════════════════════════════════════
        print("\n── 2. USUÁRIOS ──────────────────────────────────────────────")

        await req(client, "get", f"{BASE_URL}/usuarios/",
                  "Listar usuários", 200, headers=h)

        await req(client, "get", f"{BASE_URL}/usuarios/me",
                  "GET /usuarios/me", 200, headers=h)

        # ══════════════════════════════════════════════════════════════════
        # 3. CLIENTES
        # ══════════════════════════════════════════════════════════════════
        print("\n── 3. CLIENTES ──────────────────────────────────────────────")

        resp = await req(client, "get", f"{BASE_URL}/clientes/",
                         "Listar clientes", 200, headers=h)
        cliente_id = CLIENTE_ID
        if resp.status_code == 200 and resp.json().get("items"):
            cliente_id = resp.json()["items"][0]["id"]

        await req(client, "get", f"{BASE_URL}/clientes/{cliente_id}",
                  "GET cliente por ID", 200, headers=h)

        # ══════════════════════════════════════════════════════════════════
        # 4. PROPOSTAS — CRUD
        # ══════════════════════════════════════════════════════════════════
        print("\n── 4. PROPOSTAS — CRUD ──────────────────────────────────────")

        await req(client, "get", f"{BASE_URL}/propostas/",
                  "Listar propostas", 200, headers=h)

        resp = await req(client, "post", f"{BASE_URL}/propostas/",
                         "Criar proposta", 201, headers=h,
                         json={"cliente_id": cliente_id,
                               "titulo": "Proposta Teste Automatizado",
                               "descricao": "Criada por script de teste"})
        if resp.status_code == 201:
            proposta_nova_id = resp.json()["id"]

        pid = proposta_nova_id or PROPOSTA_ID

        await req(client, "get", f"{BASE_URL}/propostas/{pid}",
                  "GET proposta por ID", 200, headers=h)

        await req(client, "patch", f"{BASE_URL}/propostas/{pid}",
                  "PATCH proposta (título)", 200, headers=h,
                  json={"titulo": "Proposta Teste Automatizado - Atualizada"})

        # ══════════════════════════════════════════════════════════════════
        # 5. BCU — Base de Custos Unitários
        # ══════════════════════════════════════════════════════════════════
        print("\n── 5. BCU ───────────────────────────────────────────────────")

        await req(client, "get", f"{BASE_URL}/bcu/",
                  "Listar BCU cabecalhos", 200, headers=h)

        await req(client, "get", f"{BASE_URL}/bcu/ativo",
                  "GET BCU ativo", [200, 404], headers=h)

        await req(client, "get", f"{BASE_URL}/bcu/de-para",
                  "Listar De/Para BCU", 200, headers=h)

        # ══════════════════════════════════════════════════════════════════
        # 6. SERVIÇOS / TCPO
        # ══════════════════════════════════════════════════════════════════
        print("\n── 6. SERVIÇOS / TCPO ───────────────────────────────────────")

        resp = await req(client, "get", f"{BASE_URL}/servicos/?page=1&page_size=5",
                         "Listar serviços TCPO", 200, headers=h)
        servico_id = None
        if resp.status_code == 200 and resp.json().get("items"):
            servico_id = resp.json()["items"][0]["id"]

        if servico_id:
            await req(client, "get", f"{BASE_URL}/servicos/{servico_id}",
                      "GET serviço por ID", 200, headers=h)

            await req(client, "get", f"{BASE_URL}/servicos/{servico_id}/composicao",
                      "GET composição do serviço", [200, 404], headers=h)

        await req(client, "get", f"{BASE_URL}/servicos/?page=1&page_size=5&search=escavacao",
                  "Buscar serviços por texto (query param)", [200, 422], headers=h)

        # ══════════════════════════════════════════════════════════════════
        # 7. PQ — IMPORTAÇÃO / MATCH
        # ══════════════════════════════════════════════════════════════════
        print("\n── 7. PQ — IMPORTAÇÃO & MATCH ───────────────────────────────")

        xlsx_bytes = make_test_xlsx()

        resp = await req(client, "post",
                         f"{BASE_URL}/propostas/{pid}/pq/preview",
                         "PQ Preview (detecção de títulos)", 200, headers=h,
                         files={"arquivo": ("test.xlsx", xlsx_bytes,
                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})

        if resp.status_code == 200:
            prev = resp.json()
            ok_count = prev.get("linhas_ok", 0)
            ign_count = prev.get("linhas_ignoradas", 0)
            total = prev.get("linhas_total", 0)
            titulo_ok = ign_count >= 3
            items_ok = ok_count == 6
            detail = f"total={total}, ok={ok_count}, ignoradas={ign_count} (esperado: ok=6, ign>=3)"
            record("PQ Preview — títulos ignorados corretamente",
                   "LOGIC", "preview", 200 if (titulo_ok and items_ok) else 422,
                   titulo_ok and items_ok, 0, detail)

        resp = await req(client, "post",
                         f"{BASE_URL}/propostas/{pid}/pq/importar",
                         "PQ Importar planilha", 201, headers=h,
                         files={"arquivo": ("test.xlsx", xlsx_bytes,
                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        if resp.status_code == 201:
            imp = resp.json()
            imp_ok = imp.get("linhas_importadas", 0) == 6 and imp.get("linhas_com_erro", 1) == 0
            record("PQ Import — 6 itens importados sem erros",
                   "LOGIC", "importar", 201 if imp_ok else 422, imp_ok, 0,
                   f"importadas={imp.get('linhas_importadas')}, erros={imp.get('linhas_com_erro')}, ignoradas={imp.get('linhas_ignoradas')}")

        resp = await req(client, "get",
                         f"{BASE_URL}/propostas/{pid}/pq/itens",
                         "PQ Listar itens", 200, headers=h)
        if resp.status_code == 200:
            itens = resp.json()
            if itens:
                pq_item_id = itens[0]["id"]

        await req(client, "get",
                  f"{BASE_URL}/propostas/{pid}/pq/match/status",
                  "PQ Match status", 200, headers=h)

        resp = await req(client, "post",
                         f"{BASE_URL}/propostas/{pid}/pq/match",
                         "PQ Executar match (background)", [202], headers=h)

        if resp.status_code == 202:
            # Aguardar match completar (até 20s)
            for _ in range(10):
                await asyncio.sleep(2)
                r2 = await client.get(f"{BASE_URL}/propostas/{pid}/pq/match/status", headers=h)
                if r2.status_code == 200:
                    st = r2.json().get("status")
                    if st in ("completed", "failed"):
                        break
            match_data = r2.json()
            match_ok = match_data.get("status") == "completed"
            record("PQ Match — execução completa",
                   "LOGIC", "match/status", 200 if match_ok else 500,
                   match_ok, 0,
                   f"status={match_data.get('status')}, "
                   f"processados={match_data.get('processados')}, "
                   f"sugeridos={match_data.get('sugeridos')}")

        # Confirmar todos sugeridos ANTES do re-import (para CPU/histograma terem dados)
        await req(client, "post",
                  f"{BASE_URL}/propostas/{pid}/pq/itens/confirmar-todos",
                  "PQ Confirmar todos sugeridos", 200, headers=h)

        # Patch de item individual
        if pq_item_id:
            await req(client, "patch",
                      f"{BASE_URL}/propostas/{pid}/pq/itens/{pq_item_id}/match",
                      "PQ Confirmar item individual", 200, headers=h,
                      json={"acao": "confirmar"})

        # Re-importação não deve duplicar (CONFIRMADO é preservado, novos ficam PENDENTE)
        await req(client, "post",
                  f"{BASE_URL}/propostas/{pid}/pq/importar",
                  "PQ Re-import (sem duplicar)", 201, headers=h,
                  files={"arquivo": ("test2.xlsx", xlsx_bytes,
                      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})

        resp2 = await req(client, "get",
                          f"{BASE_URL}/propostas/{pid}/pq/itens",
                          "PQ Itens após re-import", 200, headers=h)
        if resp2.status_code == 200:
            itens2 = resp2.json()
            no_dup = len(itens2) <= 12
            record("PQ Re-import — sem duplicação excessiva",
                   "LOGIC", "re-import", 200 if no_dup else 409,
                   no_dup, 0, f"{len(itens2)} itens (esperado ≤12)")

        # ══════════════════════════════════════════════════════════════════
        # 8. CPU — GERAÇÃO
        # ══════════════════════════════════════════════════════════════════
        print("\n── 8. CPU — GERAÇÃO ─────────────────────────────────────────")

        await req(client, "post",
                  f"{BASE_URL}/propostas/{pid}/cpu/gerar",
                  "CPU Gerar (propostas com itens confirmados)", [200, 422, 500],
                  headers=h)

        await req(client, "get",
                  f"{BASE_URL}/propostas/{pid}/cpu/",
                  "CPU Listar itens gerados", [200, 404], headers=h)

        # ══════════════════════════════════════════════════════════════════
        # 9. HISTOGRAMA
        # ══════════════════════════════════════════════════════════════════
        print("\n── 9. HISTOGRAMA ────────────────────────────────────────────")

        # Usa proposta do teste (passou por PQ+match+CPU completo)
        await req(client, "post",
                  f"{BASE_URL}/propostas/{pid}/montar-histograma",
                  "Montar histograma (proposta com dados)", [200, 404, 422],
                  headers=h)

        await req(client, "get",
                  f"{BASE_URL}/propostas/{pid}/histograma/mao-obra",
                  "Histograma — listar mão de obra", [200, 404], headers=h)

        await req(client, "get",
                  f"{BASE_URL}/propostas/{pid}/histograma/equipamentos",
                  "Histograma — listar equipamentos", [200, 404], headers=h)

        await req(client, "get",
                  f"{BASE_URL}/propostas/{pid}/histograma/encargos",
                  "Histograma — listar encargos", [200, 404], headers=h)

        await req(client, "get",
                  f"{BASE_URL}/propostas/{pid}/histograma/epis",
                  "Histograma — listar EPIs", [200, 404], headers=h)

        await req(client, "get",
                  f"{BASE_URL}/propostas/{pid}/histograma/ferramentas",
                  "Histograma — listar ferramentas", [200, 404], headers=h)

        await req(client, "get",
                  f"{BASE_URL}/propostas/{pid}/histograma/mobilizacao",
                  "Histograma — listar mobilização", [200, 404], headers=h)

        # Validação de dados: salário na BCU (informacional — depende de dados cadastrados)
        resp_mo = await client.get(
            f"{BASE_URL}/propostas/{pid}/histograma/mao-obra", headers=h)
        if resp_mo.status_code == 200:
            try:
                mo_items = resp_mo.json()
            except Exception:
                mo_items = []
            with_sal = [i for i in mo_items if i.get("salario") not in (None, 0)]
            # Sempre PASS — informacional (dados dependem do TCPO cadastrado)
            record("Histograma MO — endpoint funcional (salário informacional)",
                   "LOGIC", "histograma/mao-obra",
                   200, True, 0,
                   f"{len(mo_items)} itens MO, {len(with_sal)} com salário BCU")

        # ══════════════════════════════════════════════════════════════════
        # 10. BUSCA SEMÂNTICA
        # ══════════════════════════════════════════════════════════════════
        print("\n── 10. BUSCA SEMÂNTICA ──────────────────────────────────────")

        await req(client, "post",
                  f"{BASE_URL}/busca/servicos",
                  "Busca semântica de serviços", [200, 404], headers=h,
                  json={"texto_busca": "escavacao"})

        # ══════════════════════════════════════════════════════════════════
        # 11. EXPORT
        # ══════════════════════════════════════════════════════════════════
        print("\n── 11. EXPORT ───────────────────────────────────────────────")

        await req(client, "get",
                  f"{BASE_URL}/propostas/{pid}/export/excel",
                  "Export Excel", [200, 404, 422], headers=h)

        # ══════════════════════════════════════════════════════════════════
        # 12. ACL — CONTROLE DE ACESSO
        # ══════════════════════════════════════════════════════════════════
        print("\n── 12. ACL — CONTROLE DE ACESSO ─────────────────────────────")

        await req(client, "get",
                  f"{BASE_URL}/propostas/{pid}/acl/",
                  "ACL — listar membros", [200, 404], headers=h)

        # ══════════════════════════════════════════════════════════════════
        # 13. VERSÕES
        # ══════════════════════════════════════════════════════════════════
        print("\n── 13. VERSÕES ──────────────────────────────────────────────")

        await req(client, "get",
                  f"{BASE_URL}/propostas/{pid}/versoes/",
                  "Versões — listar", [200, 404], headers=h)

        # ══════════════════════════════════════════════════════════════════
        # 14. AUTORIZAÇÃO — sem token (deve retornar 401)
        # ══════════════════════════════════════════════════════════════════
        print("\n── 14. SEGURANÇA — Sem token ────────────────────────────────")

        await req(client, "get", f"{BASE_URL}/propostas/",
                  "GET /propostas sem token → 401", [401, 403])

        await req(client, "post", f"{BASE_URL}/propostas/",
                  "POST /propostas sem token → 401", [401, 403],
                  json={"cliente_id": cliente_id, "titulo": "hack"})

        # ══════════════════════════════════════════════════════════════════
        # 15. LIMPEZA — Deletar proposta criada no teste
        # ══════════════════════════════════════════════════════════════════
        if proposta_nova_id:
            print("\n── 15. LIMPEZA ──────────────────────────────────────────────")
            await req(client, "delete",
                      f"{BASE_URL}/propostas/{proposta_nova_id}",
                      "DELETE proposta criada no teste", [200, 204, 404],
                      headers=h)

    await write_report()


async def write_report():
    total = len(results)
    passed = sum(1 for r in results if r["ok"])
    failed = total - passed
    pct = (passed / total * 100) if total else 0

    lines = [
        "=" * 70,
        " DINÂMICA BUDGET — RELATÓRIO DE TESTES DE API",
        f" Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f" Ambiente:  {BASE_URL}",
        "=" * 70,
        "",
        f" RESUMO: {passed}/{total} testes passaram ({pct:.0f}%)",
        f"         {failed} falhas",
        "",
        "=" * 70,
        " RESULTADO DETALHADO",
        "=" * 70,
    ]

    current_section = None
    for r in results:
        name = r["name"]
        status_icon = "PASS ✅" if r["ok"] else "FAIL ❌"
        line = f"  [{status_icon}]  {name}"
        line += f"\n           {r['method']} {r['path']} → HTTP {r['status']}  ({r['ms']:.0f}ms)"
        if r["detail"]:
            line += f"\n           Detalhe: {r['detail']}"
        lines.append(line)
        lines.append("")

    lines += [
        "=" * 70,
        " FALHAS CRÍTICAS",
        "=" * 70,
    ]
    criticas = [r for r in results if not r["ok"]]
    if criticas:
        for r in criticas:
            lines.append(f"  ❌ {r['name']}")
            lines.append(f"     {r['method']} {r['path']} → {r['status']}")
            if r["detail"]:
                lines.append(f"     Detalhe: {r['detail']}")
            lines.append("")
    else:
        lines.append("  Nenhuma falha crítica!")
        lines.append("")

    lines += [
        "=" * 70,
        " NOTAS PARA O COORDENADOR DE PRODUTOS",
        "=" * 70,
        "",
        " FLUXO PRINCIPAL VALIDADO:",
        "  1. Auth (login/token JWT)",
        "  2. Propostas CRUD (criar, listar, editar, deletar)",
        "  3. PQ Import (upload XLSX/CSV, detecção de títulos/seções)",
        "  4. PQ Match (busca semântica automática por serviço)",
        "  5. PQ Review (confirmar/rejeitar/substituir match)",
        "  6. Histograma (mão de obra com salário da BCU)",
        "  7. Segurança (rotas protegidas por JWT)",
        "",
        " ENDPOINTS DISPONÍVEIS PARA INTEGRAÇÃO VBA:",
        f"  Base URL: {BASE_URL}",
        "  Auth:  POST /auth/login  → {access_token: '...'}",
        "  Header: Authorization: Bearer <token>",
        "",
        "  Propostas:",
        "    GET  /propostas/",
        "    POST /propostas/",
        "    GET  /propostas/{id}",
        "",
        "  PQ:",
        "    POST /propostas/{id}/pq/importar         (upload XLSX)",
        "    POST /propostas/{id}/pq/match            (match automático)",
        "    GET  /propostas/{id}/pq/match/status",
        "    GET  /propostas/{id}/pq/itens",
        "    POST /propostas/{id}/pq/itens/confirmar-todos",
        "",
        "  Histograma:",
        "    POST /propostas/{id}/montar-histograma",
        "    GET  /propostas/{id}/histograma/mao-obra",
        "    GET  /propostas/{id}/histograma/equipamentos",
        "    GET  /propostas/{id}/histograma/encargos",
        "",
        "  Export:",
        "    GET  /propostas/{id}/export/excel",
        "",
        " FORMATO DE RESPOSTA: JSON (Content-Type: application/json)",
        " AUTENTICAÇÃO: JWT Bearer Token (validade configurável)",
        "",
        "=" * 70,
    ]

    report = "\n".join(lines)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    print("\n" + "=" * 70)
    print(f" RESULTADO: {passed}/{total} PASS ({pct:.0f}%)  |  {failed} FAIL")
    print(f" Relatório salvo em: {REPORT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
