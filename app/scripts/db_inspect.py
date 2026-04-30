import asyncio
import asyncpg
import urllib.parse
from pathlib import Path

async def main():
    env_path = Path(__file__).parents[1] / '.env'
    if not env_path.exists():
        print('ERROR: app/.env not found at', env_path)
        return
    text = env_path.read_text(encoding='utf8')
    dsn = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('DATABASE_URL='):
            dsn = line.split('=',1)[1].strip()
            break
    if not dsn:
        print('ERROR: DATABASE_URL not set in app/.env')
        return
    print('Found DATABASE_URL:', dsn)

    if dsn.startswith('postgresql+asyncpg://'):
        dsn2 = dsn.replace('postgresql+asyncpg://','')
    elif dsn.startswith('postgresql://'):
        dsn2 = dsn.replace('postgresql://','')
    else:
        dsn2 = dsn
    parsed = urllib.parse.urlparse('//' + dsn2)
    user = urllib.parse.unquote(parsed.username) if parsed.username else None
    password = urllib.parse.unquote(parsed.password) if parsed.password else None
    host = parsed.hostname or 'localhost'
    port = parsed.port or 5432
    database = parsed.path.lstrip('/') or None

    print(f'Connecting to host={host} port={port} database={database} user={user}')

    try:
        conn = await asyncpg.connect(user=user, password=password, database=database, host=host, port=port)
    except Exception as e:
        print('ERROR: could not connect to DB:', repr(e))
        return

    print('\nListing tables (excluding system schemas):')
    rows = await conn.fetch("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_type='BASE TABLE'
          AND table_schema NOT IN ('pg_catalog','information_schema')
        ORDER BY table_schema, table_name
        LIMIT 200
    """)
    for r in rows:
        print(f"{r['table_schema']}.{r['table_name']}")

    patterns = ['base_tcpo','cabecalho','usuarios','servicos','servico','bcu','cabecalho','base_tcpo','itens_proprios']
    for pat in set(patterns):
        print(f"\nSearching for tables LIKE '%{pat}%':")
        rows = await conn.fetch("SELECT table_schema, table_name FROM information_schema.tables WHERE table_type='BASE TABLE' AND table_name ILIKE $1", ('%'+pat+'%',))
        if not rows:
            print('  none')
            continue
        for r in rows:
            schema = r['table_schema']
            name = r['table_name']
            print(f'  Found: {schema}.{name}')
            try:
                cnt = await conn.fetchval(f'SELECT count(*) FROM "{schema}"."{name}"')
            except Exception as e:
                cnt = f'ERROR: {e}'
            print(f'    count: {cnt}')
            try:
                samples = await conn.fetch(f'SELECT * FROM "{schema}"."{name}" LIMIT 5')
                for s in samples:
                    print('      ', dict(s))
            except Exception as e:
                print('      sample ERROR:', e)

    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
