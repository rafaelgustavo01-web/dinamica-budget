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

    tables = ['base_tcpo','cabecalho','usuarios']
    results = {}
    for t in tables:
        try:
            cnt = await conn.fetchval(f'SELECT count(*) FROM "{t}"')
            results[t] = cnt
        except Exception as e:
            results[t] = f'ERROR: {e}'
    try:
        curdb = await conn.fetchval('SELECT current_database()')
    except Exception:
        curdb = None
    try:
        ver = await conn.fetchval('SELECT version()')
    except Exception:
        ver = None

    await conn.close()

    print('current_database:', curdb)
    print('version:', ver)
    for k,v in results.items():
        print(f'{k}: {v}')

if __name__ == '__main__':
    asyncio.run(main())
