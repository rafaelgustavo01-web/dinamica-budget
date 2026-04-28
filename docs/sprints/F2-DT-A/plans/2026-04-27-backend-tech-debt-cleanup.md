# Plano de Implementacao: Backend Tech Debt Cleanup (Sprint F2-DT-A)

**Data:** 2026-04-27
**Autor:** Supervisor (PO + Arquiteto)
**Branch:** `main` (regra global — sem feature branches)
**Worker:** claude-sonnet-4-6
**Mode:** BUILD

## 1. Contexto

Checkpoint tecnico (2026-04-27) consolidou achados de 3 analises independentes
(Amazon Q, Gemini, Kimi) em `docs/analysis/`. Esta sprint consolida o trabalho
backend de eliminacao de divida tecnica em 4 commits atomicos sequenciais.

**Pre-requisito de qualidade:** suite de regressao deve ficar **verde apos
cada commit** — nao acumular debito de teste entre commits.

## 2. Escopo

Apenas `app/backend/**`, `app/alembic/**`, `scripts/**`. Proibido tocar
`app/frontend/**` (ownership da Sprint F2-DT-B, paralela).

## 3. Contrato de API (handshake com F2-DT-B)

**FROZEN — nao alterar sem coordenar com Sprint B:**

```python
# app/backend/services/servico_catalog_service.py
class ComposicaoComponenteResponse(BaseModel):
    # ... campos existentes ...
    codigo_origem: str | None = None   # NOVO — preenchido para todos os niveis
```

Sprint B ja codifica frontend contra esse contrato.

## 4. Ordem de Tarefas (4 commits atomicos)

### Commit 1 — Pytest infra resiliente

**Arquivos:**
- `app/backend/core/config.py`
- `app/backend/tests/conftest.py`

**Mudancas:**
1. Em `Settings.model_config` adicionar `env_ignore_empty=True` para tornar
   o ambiente resiliente a variaveis vazias/invalidas no SO.
2. Em `conftest.py`: trocar engine do `db_session` para `NullPool` (sem reuso
   de conexao entre testes) e garantir `await engine.dispose()` no teardown
   da fixture de modulo.
3. Diagnosticar `connection was closed in the middle of operation` (Gemini #1)
   — se persistir apos NullPool, escopo da fixture vai a `function` por
   default e cada teste recria a sessao.

**Gate:** `python -m pytest app/backend/tests/ -q` em batch (todos os
arquivos juntos), 197+ PASS, 0 connection drops.

**Fecha:** C-03 amazonq, B-08 amazonq, Gemini #1, B-05 amazonq (parcial).

---

### Commit 2 — Purga do pipeline legado

**Arquivos:**
- `app/backend/api/v1/endpoints/admin.py` (remover branch TCPO + subprocess)
- DELETE `app/backend/services/import_preview_service.py`
- DELETE `scripts/etl_popular_base_consulta.py`

**Mudancas:**
1. Em `admin.py`: remover `import subprocess`, remover bloco
   `subprocess.run(... etl_popular_base_consulta.py ...)` (linhas ~161-180),
   remover endpoint `POST /admin/import/preview` se ainda nao foi feito 410.
2. `POST /admin/import/execute` para `source_type=TCPO` agora apenas chama
   `etl_service.parse_tcpo_pini()` + `etl_service.execute_load()` (mesmo
   caminho de `/admin/etl/upload-tcpo` + `/admin/etl/execute`).
3. Deletar `import_preview_service.py` inteiro.
4. Deletar `scripts/etl_popular_base_consulta.py`.
5. Sanitizar `Path(file.filename).suffix` antes de criar tmpfile (CWE-22).

**Gate:** `pytest -q`, regressao verde, nenhum import orfao
(`grep -r import_preview_service` retorna vazio).

**Fecha:** C-01 amazonq, C-02 amazonq, path traversal CWE-22.

---

### Commit 3 — N+1 batch + bundle

**Arquivos:**
- `app/backend/services/histograma_service.py`
- `app/backend/services/servico_catalog_service.py`
- `app/backend/services/cpu_geracao_service.py`
- `app/backend/services/proposta_versionamento_service.py`
- `app/backend/api/v1/endpoints/propostas.py`
- `app/backend/core/dependencies.py`
- `app/backend/repositories/proposta_pc_repository.py` (rename classe)
- `app/backend/services/proposta_export_service.py`

**Mudancas:**

**3.1 — N+1 -> batch (padrao SQLAlchemy 2.0):**
- `histograma_service.py:77-88` — montar set de IDs e fazer 1 query
  `SELECT * FROM de_para WHERE base_tcpo_id IN (...)` + 1 query
  `SELECT * FROM base_tcpo WHERE id IN (...)`. Idem para BCU items
  agrupados por tipo.
- `servico_catalog_service.py:listar_componentes_diretos` — substituir
  loop por `select(BaseTcpo).where(BaseTcpo.id.in_(filhos_ids))`.
- `cpu_geracao_service.py:66-71` — batch IN sobre itens PQ.
- `propostas.py:fila_aprovacoes` — coletar todos `root_id`s primeiro,
  chamar `get_papeis_bulk` 1x, filtrar local.
- `histograma_service.py:detectar_divergencias` — `asyncio.gather` das 5
  queries em paralelo (MO/EQP/EPI/FER/ENC).

**3.2 — `require_proposta_role` (`dependencies.py`):**
- Combinar 2 queries em 1 com JOIN em `proposta_acl`.
- Cache do resultado em `request.state.proposta_papel_cache[(proposta_id, user_id)]`
  para reuso intra-request.

**3.3 — Rename (`proposta_pc_repository.py`):**
- `class ProposalPcRepository` -> `class PropostaPcRepository`.
- Atualizar imports em: `histograma_service.py`,
  `proposta_versionamento_service.py`, `tests/unit/test_histograma_service.py`.

**3.4 — Fix `aceitar_valor_bcu` (`histograma_service.py`):**
- Remover `proposta.cpu_desatualizada = True` da funcao (semanticamente
  errado — aceitar BCU re-sincroniza).

**3.5 — Schema `codigo_origem` (`servico_catalog_service.py`):**
- Adicionar `codigo_origem: str | None = None` em
  `ComposicaoComponenteResponse`.
- Preencher pelo `BaseTcpo.codigo_origem` do filho carregado em batch.

**3.6 — `proposta_export_service.py`:**
- Trocar `BytesIO()` solto por `with BytesIO() as buffer:` em
  `gerar_excel` e `gerar_pdf` (CWE-400/664).
- `capa["B2"] = cliente.nome_fantasia if cliente else ""` (estava
  exibindo `proposta.codigo` com label "Cliente").

**3.7 — `proposta_versionamento_service.py` polish:**
- Mover 8 imports locais de `nova_versao` para o topo do arquivo.
- Remover `old_mob_id = mob.id` (dead code).

**Gate:** `pytest -q` verde, query log do histograma <= 15 queries para
proposta com 100 insumos (vs ~300 hoje).

**Fecha:** A-01..A-06 amazonq, M-02 amazonq, C-04 kimi, M-04 amazonq,
M-09 amazonq, M-08 amazonq (backend), A-04 amazonq, M-03 amazonq,
M-06 amazonq, B-06 amazonq, Gemini #2.

---

### Commit 4 — ETL durabilidade

**Arquivos:**
- nova migration `app/alembic/versions/0XX_etl_preview_table.py`
  (XX = proxima numeracao apos 024)
- `app/backend/services/etl_service.py`
- `app/backend/api/v1/endpoints/admin.py` (apenas `/admin/etl/*`,
  ja purgado de legado pelo Commit 2)

**Mudancas:**

1. **Migration:**
   ```sql
   CREATE TABLE etl_preview (
     token UUID PRIMARY KEY,
     source_type VARCHAR(32) NOT NULL,
     payload JSONB NOT NULL,
     created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
     expires_at TIMESTAMPTZ NOT NULL
   );
   CREATE INDEX ix_etl_preview_expires ON etl_preview(expires_at);
   ```

2. **`etl_service.py`:**
   - Remover `self._cache: dict[str, _EtlParseResult]`.
   - `parse_tcpo_pini` persiste em `etl_preview` com TTL de 1h.
   - `execute_load(token)` busca por `token` na tabela, valida
     `expires_at > now()`, executa, e deleta a linha.
   - Job de cleanup pode ficar para sprint futura (TTL passivo basta).

3. **Multi-worker safe:** comportamento testado com `--workers 2`
   (ainda que docker-compose nao tenha multi-worker hoje, contrato
   fica pronto).

**Gate:** `pytest -q`, smoke manual `upload-tcpo` -> `execute` em
container restartado entre as 2 chamadas (token sobrevive).

**Fecha:** C-03 kimi.

---

## 5. Restricoes Criticas

- **Branch `main` apenas.** Sem feature branches.
- **1 commit por etapa** com mensagem `feat(f2-dt-a/N): <descricao>`.
- **Suite verde apos cada commit** — nao deixar vermelho intermediario.
- Nao tocar em `app/frontend/**`.
- Nao marcar sprint como `DONE` — apenas `TESTED`.

## 6. Artefatos Obrigatorios Antes de TESTED

- `docs/sprints/F2-DT-A/technical-review/technical-review-2026-04-27-f2-dt-a.md`
- `docs/sprints/F2-DT-A/walkthrough/done/walkthrough-F2-DT-A.md`
- Atualizacao de `docs/shared/governance/BACKLOG.md`: F2-DT-A `TODO -> TESTED`

## 7. Fora de Escopo (parking lot — nao fazer)

- A-04 kimi (i18n hardcoded strings)
- M-04 kimi (DataTable vs MUI native)
- A-01 kimi (god classes refactor)
- B-01..B-04 amazonq (cosmeticos: `== True`, CC, function size)
- A-04 gemini (DecimalValue drift — sem evidencia de divergencia)
- A-05 amazonq (expunge clone — funciona)
- M-05 amazonq (`require_cliente_access` em versoes/homologacao — modelo
  intencional)

## 8. Itens Fechados

C-01..C-03 amazonq, A-01..A-06 amazonq, M-01/M-03/M-04/M-06/M-08bk/M-09
amazonq, B-05/B-06/B-08 amazonq, C-03/C-04 kimi, Gemini #1, Gemini #2.
**Total: 18 itens.**
