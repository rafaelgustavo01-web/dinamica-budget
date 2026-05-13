import asyncio, sys
sys.path.insert(0, '.')

PROP_ID = '0ac3ba12-ceb2-45b5-9cf5-c16225cc214a'

async def main():
    from backend.core.database import async_session_factory
    from sqlalchemy import text

    async with async_session_factory() as db:
        # Colunas da tabela pq_itens
        r = await db.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema='operacional' AND table_name='pq_itens'
            ORDER BY ordinal_position
        """))
        print("=== Colunas pq_itens ===")
        for row in r.fetchall():
            print(row)

        # Amostra de itens
        r2 = await db.execute(text("SELECT * FROM operacional.pq_itens WHERE proposta_id = :p LIMIT 3"), {"p": PROP_ID})
        rows = r2.fetchall()
        print("\n=== Amostra pq_itens ===")
        for row in rows:
            print(row)

asyncio.run(main())
