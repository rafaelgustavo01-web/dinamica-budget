import httpx, time
c = httpx.Client(base_url="http://127.0.0.1:8000", timeout=15)
r = c.post("/api/v1/auth/login", json={"email":"dinamica@easymakers.com","password":"Dinamica!Easymakers"})
h = {"Authorization": "Bearer " + r.json()["access_token"]}
PROP_ID = "0ac3ba12-ceb2-45b5-9cf5-c16225cc214a"
for i in range(120):
    try:
        rs = c.get("/api/v1/propostas/" + PROP_ID + "/pq/match/status", headers=h)
        d = rs.json()
        st = d["status"]
        print(f"[{(i+1)*5:3d}s] {st} processados={d['processados']} sugeridos={d['sugeridos']} sem_match={d['sem_match']}")
        if st in ("completed", "failed"):
            break
    except Exception as e:
        print(f"err: {e}")
    time.sleep(5)
