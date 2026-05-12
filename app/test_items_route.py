"""
Test items endpoint behavior directly using the service's Python environment.
Run with: C:\Dinamica-Budget\app\venv\Scripts\python.exe test_items_route.py
"""
import sys, asyncio
sys.path.insert(0, 'C:/Dinamica-Budget/app')

from httpx import AsyncClient, ASGITransport
from backend.main import create_app

app = create_app()

async def main():
    # Check which routes are registered
    print("=== ROUTES FOR PROPOSTAS ITEMS ===")
    for i, route in enumerate(app.routes):
        p = getattr(route, 'path', '')
        m = getattr(route, 'methods', set())
        if 'items' in p and 'propostas' in p:
            print(f'[{i}] {m} {p}')
    print(f'Total routes: {len(app.routes)}')
    print()

    # Test with a real token via httpx
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Login
        r = await client.post("/api/v1/auth/login", json={"email": "dinamica@easymakers.com", "password": "Dinamica!Easymakers"})
        print(f"Login: {r.status_code} - {r.headers.get('content-type')}")
        if r.status_code != 200:
            print(f"Login body: {r.text}")
            return
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test items endpoint
        proposta_id = "1a551def-b5e0-410e-b1a3-d1093175faca"
        r2 = await client.get(f"/api/v1/propostas/{proposta_id}/items", headers=headers)
        print(f"\nGET /items: {r2.status_code} - {r2.headers.get('content-type')}")
        print(f"Body (100): {r2.text[:100]}")

        # Test BCU epi
        r3 = await client.get(f"/api/v1/propostas/{proposta_id}/items/bcu/epi", headers=headers)
        print(f"\nGET /items/bcu/epi: {r3.status_code} - {r3.headers.get('content-type')}")
        print(f"Body (100): {r3.text[:100]}")

        # List propostas to find a valid one
        r4 = await client.get("/api/v1/propostas/", headers=headers)
        print(f"\nGET /propostas/: {r4.status_code}")
        data = r4.json()
        print(f"Total propostas: {data.get('total', 0)}")
        if data.get('items'):
            first_id = data['items'][0]['id']
            print(f"First proposta ID: {first_id}")
            r5 = await client.get(f"/api/v1/propostas/{first_id}/items", headers=headers)
            print(f"GET /items (first proposta): {r5.status_code} - {r5.headers.get('content-type')}")
            print(f"Body (200): {r5.text[:200]}")

asyncio.run(main())
