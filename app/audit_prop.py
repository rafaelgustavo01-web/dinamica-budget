import asyncio, sys
sys.path.insert(0, '.')

PROP_ID = '0ac3ba12-ceb2-45b5-9cf5-c16225cc214a'

async def main():
    from backend.core.database import async_session_factory
    from sqlalchemy import text

    async with async_session_factory() as db:
        print("=== Proposta ===")
        r = await db.execute(text("SELECT codigo, status, titulo FROM operacional.propostas WHERE id = :p"), {"p": PROP_ID})
        print(r.fetchone())

        print("\n=== PQ Importacoes ===")
        r = await db.execute(text("SELECT id, status, linhas_total, linhas_importadas FROM operacional.pq_importacoes WHERE proposta_id = :p"), {"p": PROP_ID})
        print(r.fetchall())

        print("\n=== PQ Itens por status ===")
        r = await db.execute(text("SELECT status_match, count(*) FROM operacional.pq_itens WHERE proposta_id = :p GROUP BY status_match"), {"p": PROP_ID})
        print(r.fetchall())

        print("\n=== Total PQ Itens ===")
        r = await db.execute(text("SELECT count(*) FROM operacional.pq_itens WHERE proposta_id = :p"), {"p": PROP_ID})
        print(r.scalar())

        print("\n=== Proposta Itens (cpu) ===")
        r = await db.execute(text("SELECT count(*) FROM operacional.proposta_itens WHERE proposta_id = :p"), {"p": PROP_ID})
        print(r.scalar())

        print("\n=== Histograma MO ===")
        r = await db.execute(text("SELECT count(*) FROM operacional.proposta_pc_mao_obra WHERE proposta_id = :p"), {"p": PROP_ID})
        print(r.scalar())

asyncio.run(main())
