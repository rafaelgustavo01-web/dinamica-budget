"""
Teste: upload PQ.xlsx → importar → match (poll) → CPU gerar → montar-histograma → histograma
Uso: python test_pq_upload.py [PROP_ID]
"""
import sys, json, time, pathlib

import httpx

BASE = "http://127.0.0.1:8000"
PQ_FILE = pathlib.Path(r"C:\Users\easy\Desktop\PQ.xlsx")

# Defaults — pode sobrescrever via arg
PROP_ID    = sys.argv[1] if len(sys.argv) > 1 else "0ac3ba12-ceb2-45b5-9cf5-c16225cc214a"
BCU_ID     = sys.argv[2] if len(sys.argv) > 2 else None   # se None, auto-detecta
EMAIL      = "dinamica@easymakers.com"
PASSWORD   = "Dinamica!Easymakers"
POLL_SECS  = 5      # intervalo entre polls do match
POLL_MAX   = 600    # segundos máximos de espera pelo match (PQ grande pode demorar)


def sep(label): print(f"\n── {label} ──")
def ok_fail(r, label, show_body=False):
    icon = "✅" if r.status_code < 300 else "❌"
    print(f"{icon} [{r.status_code}] {label}")
    if r.status_code >= 300 or show_body:
        try:   print(f"   {json.dumps(r.json(), ensure_ascii=False)[:600]}")
        except: print(f"   raw: {r.text[:400]}")
    return r


def login(c: httpx.Client) -> dict:
    r = c.post("/api/v1/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert r.status_code == 200, f"Login falhou: {r.text}"
    token = r.json()["access_token"]
    print(f"✅ Login OK  (token ...{token[-20:]})")
    return {"Authorization": f"Bearer {token}"}


def auto_bcu(c, h) -> str | None:
    r = c.get("/api/v1/bcu/cabecalhos", headers=h)
    if r.status_code != 200:
        print(f"   BCU erro: {r.status_code} {r.text[:200]}")
        return None
    data = r.json()
    if not data:
        return None
    return data[0]["id"]


def main():
    assert PQ_FILE.exists(), f"Arquivo não encontrado: {PQ_FILE}"

    with httpx.Client(base_url=BASE, follow_redirects=True, timeout=120) as c:
        h = login(c)
        print(f"\n{'='*60}")
        print(f"PROP: {PROP_ID}")
        print(f"FILE: {PQ_FILE.name}  ({PQ_FILE.stat().st_size/1024:.0f} KB)")
        print(f"{'='*60}")

        # ── ETAPA 1: Upload / Importar PQ ──
        sep("ETAPA 1: Importar PQ.xlsx")
        with open(PQ_FILE, "rb") as f:
            r = c.post(
                f"/api/v1/propostas/{PROP_ID}/pq/importar",
                headers=h,
                files={"arquivo": (PQ_FILE.name, f,
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
        ok_fail(r, "POST /pq/importar", show_body=(r.status_code != 201))
        if r.status_code == 201:
            imp = r.json()
            print(f"   resposta: {json.dumps(imp, ensure_ascii=False)[:400]}")
        elif r.status_code >= 400:
            print("   ⚠️  Importação falhou — abortando.")
            return 1

        # ── ETAPA 2: Match (background task → polling) ──
        sep("ETAPA 2: PQ Match")
        # verifica estado atual
        rs = c.get(f"/api/v1/propostas/{PROP_ID}/pq/match/status", headers=h)
        ms = rs.json() if rs.status_code == 200 else {}
        current = ms.get("status", "unknown")
        print(f"   estado atual: {current}")

        if current not in ("running", "queued"):
            r2 = ok_fail(c.post(f"/api/v1/propostas/{PROP_ID}/pq/match", headers=h), "POST /pq/match")
            if r2.status_code not in (200, 202):
                print("   ⚠️  Match falhou — abortando.")
                return 1

        # polling
        elapsed = 0
        while elapsed < POLL_MAX:
            time.sleep(POLL_SECS)
            elapsed += POLL_SECS
            try:
                rs = c.get(f"/api/v1/propostas/{PROP_ID}/pq/match/status", headers=h)
            except Exception as exc:
                print(f"   poll connection error: {exc} — retrying...")
                continue
            if rs.status_code != 200:
                print(f"   poll error: {rs.status_code}")
                continue
            ms = rs.json()
            st = ms.get("status")
            print(f"   [{elapsed:3d}s] status={st}  processados={ms.get('processados')}  "
                  f"sugeridos={ms.get('sugeridos')}  sem_match={ms.get('sem_match')}")
            if st == "completed":
                print("   ✅ Match concluído!")
                break
            if st == "failed":
                print(f"   ❌ Match falhou: {ms.get('error')}")
                return 1
        else:
            print(f"   ⚠️  Match não concluiu em {POLL_MAX}s — continuando mesmo assim...")

        # ── ETAPA 3: BCU ──
        sep("ETAPA 3: BCU Cabecalhos")
        bcu_id = BCU_ID or auto_bcu(c, h)
        if not bcu_id:
            print("   ❌ Nenhum BCU disponível para esta proposta.")
            return 1
        print(f"   ✅ bcu_id={bcu_id}")

        # ── ETAPA 4: CPU Gerar ──
        sep("ETAPA 4: CPU Gerar")
        r = c.post(
            f"/api/v1/propostas/{PROP_ID}/cpu/gerar",
            headers=h,
            params={"bcu_cabecalho_id": bcu_id, "percentual_bdi": 0},
        )
        ok_fail(r, "POST /cpu/gerar", show_body=(r.status_code != 200))
        if r.status_code == 200:
            body = r.json()
            print(f"   processados={body.get('processados')}  erros={body.get('erros')}  "
                  f"total_direto={body.get('total_direto')}")
        elif r.status_code >= 400:
            print("   ⚠️  CPU Gerar falhou — histograma ficará incompleto.")

        # ── ETAPA 5: Montar Histograma ──
        sep("ETAPA 5: Montar Histograma")
        r = c.post(f"/api/v1/propostas/{PROP_ID}/montar-histograma", headers=h)
        ok_fail(r, "POST /montar-histograma", show_body=True)

        # ── ETAPA 6: GET Histograma ──
        sep("ETAPA 6: GET Histograma")
        r = c.get(f"/api/v1/propostas/{PROP_ID}/histograma", headers=h)
        ok_fail(r, "GET /histograma")
        if r.status_code == 200:
            h_data = r.json()
            for k in ("mao_obra", "equipamentos", "encargos_horista", "encargos_mensalista",
                       "epis", "ferramentas", "mobilizacao", "recursos_extras", "divergencias"):
                v = h_data.get(k)
                cnt = len(v) if isinstance(v, list) else v
                print(f"   {k}: {cnt}")
            print(f"   cpu_desatualizada: {h_data.get('cpu_desatualizada')}")

        print(f"\n{'='*60}")
        print("FLUXO CONCLUÍDO")
        print(f"{'='*60}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
