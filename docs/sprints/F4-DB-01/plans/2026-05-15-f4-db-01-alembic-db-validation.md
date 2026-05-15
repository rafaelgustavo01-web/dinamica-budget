# Plano — F4-DB-01 Alembic/DB Validation Gate

## Executor
Kimi, diretamente na instância de deploy/staging indicada pelo Rafael.

## Pré-flight obrigatório
1. Confirmar branch/commit: git status --short; git rev-parse HEAD; git rev-parse origin/main.
2. Confirmar DATABASE_URL presente sem imprimir segredo; mascarar host/db/user em log.
3. Fazer backup antes de mutação: pg_dump --format=custom --file <backup-f4-db-01>.dump; validar tamanho e exit code.
4. Confirmar que o banco alvo é seguro; se for produção real, pedir OK explícito antes de downgrade ou qualquer teste destrutivo.

## Testes Alembic obrigatórios
1. Estado atual: alembic current; alembic heads; alembic history --verbose | tail -80.
2. Sanidade de árvore: verificar uma única head esperada; se houver múltiplas heads, parar e reportar.
3. Upgrade: alembic upgrade head; registrar revision final com alembic current.
4. Smoke SQL pós-upgrade: confirmar schemas operacional/referencia/bcu; confirmar tabelas F4 como operacional.smart_import_jobs e operacional.app_config; confirmar colunas críticas de cliente/numeração/staging JSONB/PQ/CPU; rodar SELECT count(*) read-only nas tabelas críticas.
5. Downgrade controlado: somente em clone/staging ou com OK explícito; executar downgrade de 1 revisão e upgrade novamente, ou usar banco temporário restaurado do dump. Se produção não permitir, marcar SKIPPED_PRODUCTION_SAFETY e compensar em banco restaurado.
6. Testes app/DB pós-upgrade: pytest tests/unit/smart_import tests/unit/test_pq_match_review.py tests/unit/test_cpu_geracao_service.py tests/unit/test_proposta_service.py -q; smoke API para criar proposta com cliente, Smart Import upload/staging/commit, match/status após limpar/reiniciar processo se possível, gerar CPU e abrir histograma.

## Critérios de aceite
- Backup feito e localizado.
- alembic upgrade head PASS.
- alembic current aponta para head esperada.
- Smoke SQL pós-upgrade PASS.
- Downgrade testado em ambiente seguro ou explicitamente marcado como SKIPPED por segurança com justificativa.
- Testes backend focados PASS.
- Relatório final em docs/sprints/F4-DB-01/technical-review/.
- Backlog só pode mover F4-DB-01 para TESTED se todos os critérios acima estiverem documentados.
