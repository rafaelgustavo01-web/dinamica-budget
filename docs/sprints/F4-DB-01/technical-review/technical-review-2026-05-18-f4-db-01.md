# Technical Review - F4-DB-01 Alembic/DB Validation Gate

Data: 2026-05-18
Executor: subagent f4-db-01-kimi-worker
Host: KVM2 (31.97.255.93)
Repo: /root/workspace/dinamica_budget

## Resultado

Status: BLOCKED / NOT TESTED.

F4-DB-01 nao deve ser movida para TESTED e F4-01..F4-05 nao devem ser promovidas para DONE por este gate.

Motivo principal: alembic upgrade head no banco seguro/staging dinamica_budget_test falhou na migration 023_bcu_unificada.py porque o tipo PostgreSQL bcu_table_type_enum ja existia antes da migration executar CREATE TYPE bcu_table_type_enum AS ENUM (...).

## Pre-flight

Branch/commit:
- HEAD: 5e2570b9986ea0201176edee772b0e90bb28113c
- origin/main: 5e2570b9986ea0201176edee772b0e90bb28113c
- Branch local alinhada ao origin/main.
- Worktree inicial tinha arquivos nao rastreados fora do escopo: docs/SMART_IMPORT_USER_GUIDE.md, docs/analysis/*.md, docs/sprints/F4-06/dispatch/, scripts/ml_training_loop.py, scripts/pq_auto_training.py.

Observacao: ao final tambem havia modificacoes em arquivos fora do escopo, nao feitas manualmente por este worker e nao revertidas:
- app/backend/services/smart_import_service.py
- app/backend/tests/unit/smart_import/test_smart_import_service.py
- app/frontend/src/features/bcu/BcuUploadPage.tsx

DATABASE_URL:
- Nao havia .env presente no repo remoto, apenas .env.example.
- O default em app/backend/core/config.py aponta para banco local dinamica_budget, mas esse banco nao existe no PostgreSQL da KVM2.
- Bancos locais encontrados: dinamica_budget_test, dinamica_budget_test_f4_02, postgres.
- Para a validacao foi usado dinamica_budget_test como alvo seguro/staging.
- URL mascarada: postgresql+asyncpg://<user>:<password>@<host>:<port>/<db>

Seguranca do alvo:
- Alvo usado: dinamica_budget_test, banco local de teste/staging.
- Nao havia processo FastAPI/uvicorn/gunicorn ativo nem portas 8000/3000/8080 escutando.
- Nenhum deploy ou restart foi executado.

Backup:
- Arquivo: /root/workspace/dinamica_budget/backups/backup-f4-db-01-2026-05-18-dinamica_budget_test.dump
- Formato: pg_dump --format=custom
- Tamanho: 2117 bytes
- Exit code: 0
- O primeiro pg_dump tentou gravar diretamente em backups/ como usuario postgres e falhou por permissao antes de qualquer mutation. Em seguida o dump foi gerado em /tmp, movido para backups/ e validado.

## Alembic

Estado antes do upgrade:
- alembic current: sem revisao registrada inicialmente.
- alembic heads: 034_app_config (head).
- Sanidade da arvore: PASS, havia uma unica head.

Upgrade:
- Comando: alembic upgrade head
- Resultado: FAIL

Trecho relevante:
    Running upgrade 022 -> 023, Add BCU schema and deprecate pc_tabelas
    psycopg2.errors.DuplicateObject: type "bcu_table_type_enum" already exists
    SQL: CREATE TYPE bcu_table_type_enum AS ENUM ('MO', 'EQP', 'EPI', 'FER', 'MOB')

Arquivo causador:
- app/alembic/versions/023_bcu_unificada.py
- Linha logica: op.execute("CREATE TYPE bcu_table_type_enum AS ENUM ('MO', 'EQP', 'EPI', 'FER', 'MOB')")

O dump pre-flight ja continha o tipo public.bcu_table_type_enum, entao a migration 023 nao e idempotente para este estado real/staging.

Estado pos-falha antes do restore:
- alembic current: 021
- Schemas existentes: bcu, operacional, referencia
- bcu_table_type_enum: existe
- bcu sem tabelas criadas pela migration 023
- operacional.smart_import_jobs: ausente imediatamente apos falha do upgrade
- operacional.app_config: ausente imediatamente apos falha do upgrade

O banco dinamica_budget_test foi restaurado ao estado pre-flight usando o dump criado antes da validacao para nao deixar o alvo parcialmente migrado.

Estado apos restore:
- Schemas: bcu, operacional, referencia
- public.alembic_version: ausente
- public.bcu_table_type_enum: existe
- Tabelas nos schemas operacional/referencia/bcu/public: 0

## Smoke SQL

Smoke pos-upgrade completo: BLOCKED.

Motivo: alembic upgrade head nao chegou ao head 034_app_config.

Evidencias coletadas antes do restore:
- Schemas operacional, referencia, bcu presentes.
- operacional.smart_import_jobs ausente imediatamente apos falha.
- operacional.app_config ausente imediatamente apos falha.
- bcu_table_type_enum presente antes da migration 023, causando colisao.

Consultas de colunas criticas ficaram inconclusivas como validacao de head porque o banco nao atingiu 034_app_config.

## Downgrade Controlado

Status: BLOCKED.

Motivo: o banco nao chegou ao head; portanto nao havia estado valido para downgrade de 1 revisao e re-upgrade.

Nao foi feito drop/reset destrutivo de banco real. O unico restore foi no banco local de teste dinamica_budget_test, a partir do backup pre-flight, para desfazer a validacao parcial.

## Testes Backend Focados

Comando executado:
pytest backend/tests/unit/smart_import backend/tests/unit/test_pq_match_review.py backend/tests/unit/test_cpu_geracao_service.py backend/tests/unit/test_proposta_service.py -q

Resultado:
- 87 passed
- 14 errors
- 1 warning

Falha principal:
- asyncpg.exceptions.UndefinedColumnError: column "razao_social" of relation "clientes" does not exist

Tambem ocorreram erros de teardown tentando dropar referencia.base_tcpo com dependencias existentes.

Interpretacao: a suite confirma desalinhamento entre ORM/testes F4 e schema disponivel quando o Alembic nao chega ao head. O resultado nao pode ser usado como validacao pos-upgrade.

## API Smoke

Status: BLOCKED / NOT RUN.

Motivos:
- alembic upgrade head falhou antes de head.
- Nao havia processo de aplicacao ativo detectado.
- Guardrail proibe deploy/restart sem OK explicito.

Fluxos nao executados:
- criacao de proposta com cliente
- Smart Import upload/staging/commit
- match/status
- geracao de CPU
- abertura de histograma

## Conclusao

Criterios de aceite:
- Backup feito e localizado: PASS
- alembic upgrade head: FAIL
- alembic current no head esperado: FAIL
- Smoke SQL pos-upgrade: BLOCKED
- Downgrade/re-upgrade controlado: BLOCKED
- Testes backend focados: FAIL (87 passed, 14 errors)
- API smoke: BLOCKED
- Relatorio final: PASS

## Recomendacao tecnica

Corrigir app/alembic/versions/023_bcu_unificada.py para tratar bcu_table_type_enum de forma idempotente no estado real/staging. Direcao sugerida: criar o tipo com bloco DO BEGIN/EXCEPTION duplicate_object ou mecanismo SQLAlchemy/PostgreSQL com checkfirst=True, preservando compatibilidade com o downgrade.

Depois disso, repetir o gate completo desde backup novo:
1. alembic current
2. alembic upgrade head
3. smoke SQL de schemas/tabelas/colunas F4
4. testes focados
5. smoke API se a aplicacao estiver rodando ou houver OK explicito para subir/reiniciar servico
6. downgrade/re-upgrade somente em clone/staging

## Observacao final de worktree

Git status observado na verificacao final continha modificacoes fora do escopo deste worker, nao revertidas:
- app/backend/api/v1/endpoints/pq_importacao.py
- app/backend/api/v1/endpoints/smart_import.py
- app/backend/services/smart_import_service.py
- app/backend/tests/conftest.py
- app/backend/tests/unit/smart_import/test_smart_import_service.py
- app/frontend/src/features/bcu/BcuUploadPage.tsx

Tambem permaneceu como nao rastreado o diretorio deste relatorio: docs/sprints/F4-DB-01/technical-review/.

Atualizacao apos commit/push: nova verificacao de git status mostrou apenas arquivos nao rastreados ja fora do escopo (docs/SMART_IMPORT_USER_GUIDE.md, docs/analysis/*.md, scripts/ml_training_loop.py, scripts/pq_auto_training.py). As modificacoes listadas acima nao estavam mais presentes nessa verificacao final.
