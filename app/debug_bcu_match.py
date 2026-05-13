import asyncio, sys, unicodedata
sys.path.insert(0, '.')

async def main():
    from backend.core.config import settings
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text
    e = create_async_engine(settings.DATABASE_URL)
    async with e.connect() as c:
        r = await c.execute(text("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'operacional' AND table_name = 'proposta_pc_mao_obra'
            ORDER BY ordinal_position
        """))
        print('Columns of operacional.proposta_pc_mao_obra:')
        for row in r.fetchall():
            print(f'  {row[0]} ({row[1]})')

asyncio.run(main())
