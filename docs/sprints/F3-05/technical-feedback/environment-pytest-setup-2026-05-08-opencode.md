# Environment Setup — Pytest — Opencode

## Resultado
OK

## Ambiente criado/usado
- Python 3.12.3 (sistema: `/usr/bin/python3`)
- Ambiente virtual local criado em: `/root/workspace/dinamica_budget/app/.venv`
- Diretório de trabalho para execução dos testes: `/root/workspace/dinamica_budget/app`

## Pacotes instalados
Instalação em duas etapas:

1. **Mínimos iniciais** (para viabilizar pytest e imports básicos):
   - pytest==8.3.4
   - pytest-asyncio==0.24.0
   - pytest-cov==6.0.0
   - httpx==0.28.1
   - openpyxl==3.1.5
   - rapidfuzz==3.10.1
   - pydantic==2.10.3
   - pydantic-settings==2.6.1
   - pydantic[email]==2.10.3
   - sqlalchemy[asyncio]==2.0.36

2. **Completo via `requirements.txt`** (necessário porque os módulos do backend importam fastapi, passlib, torch, sentence-transformers, etc.):
   - fastapi==0.115.5
   - uvicorn[standard]==0.32.1
   - python-multipart==0.0.12
   - asyncpg==0.30.0
   - psycopg2-binary==2.9.11
   - alembic==1.14.0
   - pgvector==0.3.6
   - passlib[bcrypt]==1.7.4
   - bcrypt==4.0.1
   - python-jose[cryptography]==3.3.0
   - slowapi==0.1.9
   - sentence-transformers==3.3.1
   - torch>=2.5.1
   - structlog==24.4.0
   - python-dotenv==1.0.1
   - pgcli==4.4.0
   - reportlab>=4.0.0
   - (e respectivas dependências transitivas: numpy, scipy, scikit-learn, transformers, huggingface-hub, tokenizers, safetensors, triton, nvidia-*, etc.)

## Comandos executados

```bash
# Criação do venv
python3 -m venv .venv

# Upgrade pip
.venv/bin/pip install --upgrade pip

# Instalação mínima inicial
.venv/bin/pip install pytest==8.3.4 pytest-asyncio==0.24.0 pytest-cov==6.0.0 httpx==0.28.1 openpyxl==3.1.5 rapidfuzz==3.10.1 pydantic==2.10.3 pydantic-settings==2.6.1 pydantic[email]==2.10.3 sqlalchemy[asyncio]==2.0.36

# Instalação completa do projeto
.venv/bin/pip install -r requirements.txt

# Verificação do pytest
.venv/bin/python -m pytest --version

# Execução dos testes focados F3-05
.venv/bin/python -m pytest backend/tests/unit/test_pq_import_service.py backend/tests/unit/test_pq_match_service.py backend/tests/unit/test_etl_service.py backend/tests/unit/test_explosao_recursiva.py -v
```

## Resultado dos testes

**22 passed, 3 warnings in 0.50s**

Detalhamento:
- `test_pq_import_service.py`: 3 passed
- `test_pq_match_service.py`: 1 passed
- `test_etl_service.py`: 9 passed
- `test_explosao_recursiva.py`: 9 passed

Warnings observados:
1. `PytestDeprecationWarning` do `pytest-asyncio` sobre `asyncio_default_fixture_loop_scope` não configurado — não bloqueante.
2. `DeprecationWarning` do `passlib` sobre `crypt` — proveniente da lib bcrypt/passlib, não bloqueante.
3. `RuntimeWarning` em `test_explodir_sub_composicao_cria_netos_sem_duplicar` e `test_explodir_sub_composicao_suporta_item_proprio`: coroutine `AsyncMockMixin._execute_mock_call` nunca foi awaited no código de produção `cpu_explosao_service.py:198` — indica mock não totalmente aguardado em teste unitário, mas não quebra a execução.

## Pendências
1. **pytest.ini**: adicionar `asyncio_default_fixture_loop_scope = function` para eliminar o deprecation warning do pytest-asyncio.
2. **test_explosao_recursiva.py**: revisar mocks de `AsyncMock` no `cpu_explosao_service.py` para garantir que corotinas sejam devidamente awaited nos testes que disparam o warning.
3. **Dependências pesadas**: torch + sentence-transformers + nvidia-* somam ~2.5 GB. Para CI/QA mais enxuto, avaliar se testes unitários podem rodar com um requirements de teste reduzido (sem libs de ML/embeddings), já que os testes focados mockam os serviços ML.
4. **Ambiente de banco**: testes unitários não exigiram conexão ativa com PostgreSQL nesta execução. Testes de integração/end-to-end podem requerer banco de dados de teste configurado.
