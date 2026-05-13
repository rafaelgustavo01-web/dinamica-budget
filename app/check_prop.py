import asyncio, sys
sys.path.insert(0, '.')

PROP_ID = '0ac3ba12-ceb2-45b5-9cf5-c16225cc214a'

async def main():
    from backend.core.database import async_session_factory
    from sqlalchemy import text

    async with async_session_factory() as db:
        r = await db.execute(text("SELECT codigo, status, titulo FROM operacional.propostas WHERE id = :p"), {"p": PROP_ID})
        print("Proposta:", r.fetchone())

        r2 = await db.execute(text("SELECT status_match, count(*) as n FROM operacional.pq_itens WHERE proposta_id = :p GROUP BY status_match"), {"p": PROP_ID})
        print("PQ itens por status:", r2.fetchall())

        r3 = await db.execute(text("SELECT count(*) FROM operacional.proposta_itens WHERE proposta_id = :p"), {"p": PROP_ID})
        print("Proposta itens (cpu):", r3.scalar())

        r4 = await db.execute(text("SELECT count(*) FROM operacional.proposta_pc_mao_obra WHERE proposta_id = :p"), {"p": PROP_ID})
        print("Histograma MO rows:", r4.scalar())

asyncio.run(main())
