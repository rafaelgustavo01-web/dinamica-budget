"""
Teste end-to-end COMPLETO: PQ Match → CPU Gerar → Histograma para PROP-2026-0007
"""
import sys, json
sys.path.insert(0, '.')

import httpx

BASE = "http://127.0.0.1:8000"
PROP_ID = "0ac3ba12-ceb2-45b5-9cf5-c16225cc214a"


def login(c: httpx.Client) -> dict:
    r = c.post(f"{BASE}/api/v1/auth/login", json={"email": "dinamica@easymakers.com", "password": "Dinamica!Easymakers"})
    assert r.status_code == 200, f"Login falhou: {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def step(label, r: httpx.Response, show_body=False):
    ok = "✅" if r.status_code < 300 else "❌"
    print(f"{ok} [{r.status_code}] {label}")
    if r.status_code >= 300 or show_body:
        try:
            body = r.json() if r.content else {}
            print(f"   {json.dumps(body, ensure_ascii=False)[:400]}")
        except Exception:
            print(f"   raw: {r.text[:200]}")
    return r


def main():
    with httpx.Client(base_url=BASE, follow_redirects=True, timeout=60) as c:
        headers = login(c)
        print(f"\n{'='*60}")
        print(f"PROP-2026-0007 | {PROP_ID}")
        print(f"{'='*60}\n")

        # ── ETAPA 1: Estado do match ──
        print("── ETAPA 1: PQ Match ──")
        r = step("GET /pq/match/status", c.get(f"/api/v1/propostas/{PROP_ID}/pq/match/status", headers=headers))
        if r.status_code == 200:
            ms = r.json()
            s = ms.get("status")
            print(f"   status={s} processados={ms.get('processados')} sugeridos={ms.get('sugeridos')} sem_match={ms.get('sem_match')}")
            if s == "not_started":
                print("   → Disparando match...")
                r2 = step("POST /pq/match", c.post(f"/api/v1/propostas/{PROP_ID}/pq/match", headers=headers))
                print(f"   → Retornou {r2.json()} (background task enfileirado)")

        # ── ETAPA 2: BCU disponíveis ──
        print("\n── ETAPA 2: BCU Cabecalhos ──")
        r = step("GET /bcu/cabecalhos", c.get("/api/v1/bcu/cabecalhos", headers=headers))
        bcu_id = None
        if r.status_code == 200 and r.content:
            try:
                bcus = r.json()
                lst = bcus if isinstance(bcus, list) else bcus.get("items", bcus.get("data", []))
                for b in lst[:3]:
                    print(f"   id={b.get('id')} desc={b.get('descricao') or b.get('nome') or b.get('titulo')}")
                if lst:
                    bcu_id = lst[0].get("id")
            except Exception as e:
                print(f"   parse error: {e}")

        # ── ETAPA 3: CPU Gerar ──
        print("\n── ETAPA 3: CPU Gerar ──")
        cpu_url = f"/api/v1/propostas/{PROP_ID}/cpu/gerar"
        params = {"percentual_bdi": "0"}
        if bcu_id:
            params["bcu_cabecalho_id"] = bcu_id
            print(f"   usando bcu_cabecalho_id={bcu_id}")
        r = step("POST /cpu/gerar", c.post(cpu_url, headers=headers, params=params))
        if r.status_code == 200 and r.content:
            try:
                cpu = r.json()
                print(f"   total_direto={cpu.get('total_direto')} total_geral={cpu.get('total_geral')}")
                det = cpu.get("detalhe", {})
                print(f"   processados={det.get('processados')} erros={det.get('erros')}")
            except Exception as e:
                print(f"   parse error: {e}")

        # ── ETAPA 4: Montar histograma ──
        print("\n── ETAPA 4: Montar Histograma ──")
        r = step("POST /montar-histograma", c.post(f"/api/v1/propostas/{PROP_ID}/montar-histograma", headers=headers))
        if r.status_code == 200 and r.content:
            try:
                h = r.json()
                print(f"   resultado: {json.dumps(h, ensure_ascii=False)[:300]}")
            except Exception:
                print(f"   raw: {r.text[:200]}")

        # ── ETAPA 5: Ver histograma ──
        print("\n── ETAPA 5: GET Histograma ──")
        r = step("GET /histograma", c.get(f"/api/v1/propostas/{PROP_ID}/histograma", headers=headers))
        if r.status_code == 200 and r.content:
            try:
                h = r.json()
                if isinstance(h, list):
                    print(f"   {len(h)} linhas no histograma")
                    if h:
                        print(f"   Primeira linha keys: {list(h[0].keys())}")
                else:
                    print(f"   keys: {list(h.keys())}")
                    for k, v in h.items():
                        if isinstance(v, list):
                            print(f"   {k}: {len(v)} items")
                        else:
                            print(f"   {k}: {v}")
            except Exception as e:
                print(f"   parse error: {e}")

        print(f"\n{'='*60}")
        print("FLUXO CONCLUÍDO")
        print(f"{'='*60}")


main()
