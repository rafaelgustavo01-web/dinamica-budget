import asyncio, sys
sys.path.insert(0, '.')

async def main():
    from backend.core.config import settings
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy import text
    e = create_async_engine(settings.DATABASE_URL)
    async with e.connect() as c:
        # Active BCU
        r = await c.execute(text("SELECT id, nome_arquivo, is_ativo FROM bcu.cabecalho WHERE is_ativo=true"))
        rows = r.fetchall()
        print('Active BCU:', rows)
        if rows:
            cab_id = rows[0][0]
            r2 = await c.execute(text("SELECT descricao_funcao, salario, custo_unitario_h FROM bcu.mao_obra_item WHERE cabecalho_id=:cid LIMIT 8"), {"cid": cab_id})
            print('BCU MO (active cab):')
            for row in r2.fetchall():
                print(f'  {row[0]!r} sal={row[1]} h={row[2]}')

        # De/Para count
        r3 = await c.execute(text("""
            SELECT COUNT(*) FROM referencia.bcu_de_para bdp
            JOIN operacional.proposta_item_composicoes pic ON pic.insumo_base_id = bdp.base_tcpo_id
            JOIN operacional.proposta_itens pi ON pi.id = pic.proposta_item_id
            WHERE pi.proposta_id = '809c4e22-5672-4829-8fcc-d967de0e7817'
        """))
        print('De/Para matches for proposta:', r3.scalar())

        # Check actual inserted salario for "Ajudante"
        r4 = await c.execute(text("""
            SELECT descricao_funcao, salario, custo_unitario_h, bcu_item_id
            FROM operacional.proposta_pc_mao_obra
            WHERE proposta_id='809c4e22-5672-4829-8fcc-d967de0e7817'
            AND descricao_funcao IN ('Ajudante','AJUDANTE','AUX. SERVICOS GERAIS','AUX. SERVIÇOS GERAIS')
        """))
        print('Ajudante rows:')
        for row in r4.fetchall():
            print(f'  {row[0]!r} sal={row[1]} h={row[2]} bcu={str(row[3])[:8] if row[3] else None}')

asyncio.run(main())
