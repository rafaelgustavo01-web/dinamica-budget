import asyncio, sys, unicodedata
sys.path.insert(0, '.')

def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()

async def main():
    from backend.core.config import settings
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.connect() as c:
        r = await c.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='proposta' ORDER BY 1"))
        print("Tables proposta:", [row[0] for row in r.fetchall()])
        
        r2 = await c.execute(text("SELECT DISTINCT descricao, tipo_recurso FROM referencia.base_tcpo WHERE tipo_recurso='MO' LIMIT 8"))
        tcpo = r2.fetchall()
        print("TCPO MO sample:", [(row[0], row[1]) for row in tcpo])
        
        r3 = await c.execute(text("SELECT descricao_funcao, salario FROM bcu.mao_obra_item LIMIT 8"))
        bcu = r3.fetchall()
        print("BCU MO sample:", [(row[0], row[1]) for row in bcu])
        
        # Try matching
        bcu_names = {norm(row[0]): row[1] for row in bcu}
        print("\nNorm match test:")
        for tcpo_row in tcpo[:5]:
            n = norm(tcpo_row[0])
            sal = bcu_names.get(n)
            print(f"  TCPO: {tcpo_row[0]!r} -> norm: {n!r} -> BCU sal: {sal}")
        
        # Check histograma pc_mao_obra
        r4 = await c.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='proposta' AND tablename LIKE '%mao%'"))
        print("\nMaoObra tables:", [row[0] for row in r4.fetchall()])

asyncio.run(main())
