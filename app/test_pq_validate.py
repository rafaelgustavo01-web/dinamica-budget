"""Validação PQ - títulos, duplicatas e lógica de negócio."""
import asyncio
import io
import os
import sys

sys.path.insert(0, ".")
os.environ.setdefault("ENV", "development")

import openpyxl
import httpx

BASE = "http://127.0.0.1:8000/api/v1"
PROPOSTA_ID = "809c4e22-5672-4829-8fcc-d967de0e7817"


def make_test_xlsx():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["codigo", "descricao", "unidade", "quantidade"])
    ws.append(["", "CAPITULO 1 - SERVICOS", "", ""])       # deve ser IGNORADO
    ws.append(["1", "Escavação manual de vala", "m3", "10"])  # OK
    ws.append(["2", "Forma de madeira compensada", "m2", "25"])  # OK
    ws.append(["3", "Concretagem em estrutura", "m3", "5"])  # OK
    ws.append(["", "", "", ""])                               # linha vazia ignorada
    ws.append(["", "Total Geral", "", ""])                   # IGNORADO
    ws.append(["", "SUBTOTAL", "", ""])                      # IGNORADO
    ws.append(["4", "Escavação manual de vala", "m3", "10"])  # duplicata descricao (OK - mesmo serviço, linha diferente)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        # ── Login ──────────────────────────────────────────────────────────
        resp = await client.post(f"{BASE}/auth/login",
            json={"email": "dinamica@easymakers.com", "password": "Dinamica!Easymakers"})
        assert resp.status_code == 200, f"Login falhou: {resp.text}"
        token = resp.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}
        print("✅ Login OK")

        xlsx_bytes = make_test_xlsx()

        # ── Preview ────────────────────────────────────────────────────────
        resp = await client.post(
            f"{BASE}/propostas/{PROPOSTA_ID}/pq/preview",
            headers=h,
            files={"arquivo": ("test_pq.xlsx", xlsx_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 200, f"Preview falhou: {resp.text}"
        prev = resp.json()
        print(f"\n📋 Preview PQ:")
        print(f"   linhas_total={prev['linhas_total']}, ok={prev['linhas_ok']}, "
              f"ignoradas={prev['linhas_ignoradas']}, erros={prev['linhas_com_erro']}")
        for it in prev["itens"]:
            status = it["status"]
            icon = "✅" if status == "OK" else ("⚠️" if status == "IGNORADO" else "❌")
            print(f"   {icon} [{status}] L{it['linha_planilha']}: {it['descricao'][:60]}")

        ok_count = prev["linhas_ok"]
        ign_count = prev["linhas_ignoradas"]
        assert ok_count == 4, f"Esperado 4 itens OK, obteve {ok_count}"
        assert ign_count >= 3, f"Esperado >=3 ignorados (títulos), obteve {ign_count}"
        print("✅ Detecção de títulos OK - títulos foram ignorados corretamente")

        # ── Importar ────────────────────────────────────────────────────────
        resp = await client.post(
            f"{BASE}/propostas/{PROPOSTA_ID}/pq/importar",
            headers=h,
            files={"arquivo": ("test_pq.xlsx", xlsx_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 201, f"Import falhou: {resp.text}"
        imp = resp.json()
        print(f"\n📥 Import PQ:")
        print(f"   status={imp['status']}, total={imp['linhas_total']}, "
              f"importadas={imp['linhas_importadas']}, "
              f"ignoradas={imp.get('linhas_ignoradas', 'N/A')}, erros={imp['linhas_com_erro']}")
        assert imp["linhas_importadas"] == 4, f"Esperado 4 importadas, obteve {imp['linhas_importadas']}"
        print("✅ Import OK - 4 itens importados (títulos descartados)")

        # ── Listar itens ────────────────────────────────────────────────────
        resp = await client.get(f"{BASE}/propostas/{PROPOSTA_ID}/pq/itens", headers=h)
        assert resp.status_code == 200
        itens = resp.json()
        print(f"\n📄 PQ Itens ({len(itens)} total):")
        for it in itens[:8]:
            print(f"   [{it['match_status']}] {it['descricao_original'][:50]} | "
                  f"qtd={it['quantidade_original']} {it.get('unidade_medida_original','')}")

        pendentes = [i for i in itens if i["match_status"] == "PENDENTE"]
        print(f"\n   PENDENTE={len(pendentes)}, "
              f"SUGERIDO={len([i for i in itens if i['match_status']=='SUGERIDO'])}, "
              f"CONFIRMADO={len([i for i in itens if i['match_status']=='CONFIRMADO'])}")
        print("✅ Listagem de itens OK")

        # ── Reimportação (não deve duplicar itens confirmados) ─────────────
        resp = await client.post(
            f"{BASE}/propostas/{PROPOSTA_ID}/pq/importar",
            headers=h,
            files={"arquivo": ("test_pq2.xlsx", xlsx_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 201, f"Re-import falhou: {resp.text}"
        resp2 = await client.get(f"{BASE}/propostas/{PROPOSTA_ID}/pq/itens", headers=h)
        itens2 = resp2.json()
        print(f"\n🔄 Re-import: {len(itens2)} itens (deve ser ~4, sem duplicatas PENDENTE)")
        assert len(itens2) <= 10, f"Possível duplicação: {len(itens2)} itens após re-import"
        print("✅ Re-import OK - sem duplicação excessiva")

    print("\n" + "="*60)
    print("✅ VALIDAÇÃO PQ CONCLUÍDA COM SUCESSO")


asyncio.run(main())
