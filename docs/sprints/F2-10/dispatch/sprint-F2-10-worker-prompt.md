# Worker Prompt — Sprint F2-10

**Para:** Kimi K2.6
**Modo:** Agent / BUILD / Always Proceed
**Sprint:** F2-10 — BCU Unificada (Base de Custos Unitários) + De/Para
**Repo:** C:\Users\rafae\Documents\workspace\github\dinamica-budget
**Prioridade:** P1 — abre Milestone 7

---

Você é o worker da Sprint F2-10. Implemente o plano completo em `docs/sprints/F2-10/plans/2026-04-27-bcu-unificada-de-para.md` do início ao fim sem pausas.

Use `superpowers:subagent-driven-development` ou `superpowers:executing-plans` para executar o plano task-a-task com checkboxes.

## Por que você foi escolhido

Esta sprint é **predominantemente backend**:

- **Migration 023**: schema `bcu` com 11 tabelas (10 dados + de_para), drop de 11 tabelas `pc_*`, nova FK em `propostas`
- **Dois services novos**: `BcuService` (importação + sync 2 schemas) e `BcuDeParaService` (CRUD + validação polimórfica de tipo)
- **Refatoração `cpu_custo_service`**: lógica de lookup substituída (heurístico → De/Para explícito com fallback)
- **~35 testes novos** sobre base de 179 (F2-09)
- Frontend: 2 novas páginas + 4 arquivos de modificação — escopo controlado

## Instruções de execução

1. **OBRIGATÓRIO antes de codar**: leia em ordem os 13 arquivos listados em "Pré-requisito de leitura" no briefing
2. Leia o briefing: `docs/sprints/F2-10/briefing/sprint-F2-10-briefing.md`
3. Leia o plano completo: `docs/sprints/F2-10/plans/2026-04-27-bcu-unificada-de-para.md`
4. Execute cada task em ordem, commitando após cada uma
5. Após cada task de backend: `cd app && python -m pytest backend/tests/ -v --tb=short`
6. Após cada task de frontend: `cd app/frontend && npx tsc --noEmit`
7. Ao concluir TODAS as tasks:
   - Crie `docs/sprints/F2-10/technical-review/technical-review-2026-04-27-f2-10.md`
   - Crie `docs/sprints/F2-10/walkthrough/done/walkthrough-F2-10.md`
   - Atualize F2-10 para **TESTED** em `docs/shared/governance/BACKLOG.md`

## Atenções especiais

- **FK polimórfica em `bcu.de_para`**: `bcu_item_id` NÃO tem FK física no PostgreSQL — aponta para 5 tabelas distintas. A integridade é garantida inteiramente no `BcuDeParaService.criar`: antes de persistir, execute um SELECT na tabela correspondente ao `bcu_table_type` para validar que o UUID existe.

- **Índice parcial UNIQUE `is_ativo`**:
  ```sql
  CREATE UNIQUE INDEX ix_bcu_cabecalho_ativo ON bcu.cabecalho (is_ativo) WHERE is_ativo = TRUE;
  ```
  No service `ativar_cabecalho`: primeiro `UPDATE bcu.cabecalho SET is_ativo=FALSE WHERE is_ativo=TRUE`, depois `UPDATE bcu.cabecalho SET is_ativo=TRUE WHERE id=:id`. Tudo em uma transação.

- **Re-importação idempotente por `codigo_origem`**:
  - `BcuService.importar_bcu` faz UPSERT (INSERT ... ON CONFLICT (codigo_origem) DO UPDATE) tanto em `bcu.*` quanto em `referencia.base_tcpo`
  - `codigo_origem` derivado: `BCU-MO-001` ... `BCU-MO-NNN` (sequencial por aba, 3 dígitos 0-padded)
  - Encargos e Mobilização **NÃO** geram `codigo_origem` (não entram em De/Para)

- **Validação de tipo coerente (De/Para)**:
  ```python
  TIPO_COERENCIA = {
      "MO": ["MO"],
      "EQUIPAMENTO": ["EQP"],
      "INSUMO": ["EPI", "FER"],
      "FERRAMENTA": ["FER"],
  }
  ```
  `BaseTcpo.tipo_recurso` (campo existente) deve estar dentro do conjunto válido para o `bcu_table_type` solicitado. Violação → `HTTPException(422, "Tipo incoerente: TCPO {tipo} não pode mapear para BCU {bcu_table_type}")`.

- **Renomear `pc_cabecalho_id` → `bcu_cabecalho_id`** em todo o código:
  ```bash
  rg "pc_cabecalho_id" app/ --files-with-matches
  ```
  Arquivos esperados: `cpu_geracao_service.py`, `proposta_repository.py`, `schemas/proposta.py`, `proposalsApi.ts`. Renomear todos antes do Task 5.

- **Ordem de rotas FastAPI** em `bcu.py`:
  ```python
  # Rotas estáticas ANTES de rotas com parâmetros
  GET  /bcu/cabecalho-ativo          # antes de /{cabecalho_id}/...
  GET  /bcu/de-para                  # antes de /{cabecalho_id}/...
  POST /bcu/de-para
  PATCH /bcu/de-para/{id}
  DELETE /bcu/de-para/{id}
  GET  /bcu/{cabecalho_id}/mao-obra  # parametrizadas por último
  ```

- **Endpoint deprecado em `admin.py`**: `POST /admin/etl/upload-converter` → remover completamente. `POST /admin/import/execute` com `source_type=PC` → retornar `410 Gone` com body `{"detail": "Use POST /bcu/importar para importar a BCU"}`.

- **Deletar arquivos obsoletos com segurança**: antes de deletar qualquer arquivo, confirme com `rg "from.*pc_tabelas" app/ --files-with-matches` que nenhum import restante aponta para ele. Sequência recomendada: substituir imports → verificar tsc + pytest → deletar arquivo morto.

- **BcuDeParaPage — selects encadeados**: o select de "item BCU" deve ser carregado de forma dinâmica conforme o tipo selecionado. Use `GET /bcu/{cabecalho_ativo_id}/{tipo}` para buscar os itens do tipo. Cache com TanStack Query por `[bcu_item_type, cabecalho_id]`.

- **Testes 200+ PASS**: meta estrita. Base é 179 (F2-09). Adicionar ≥ 25:
  - `test_bcu_service.py`: 10 testes (importação, idempotência, sync base_tcpo, ativar)
  - `test_bcu_de_para_service.py`: 8 testes (CRUD, validação tipo, UniqueConstraint, lookup)
  - `test_bcu_endpoints.py`: 12 testes (auth, importar, ativar, listar, De/Para CRUD, 410 Gone)
  - `test_cpu_custo_service.py`: +5 testes (lookup via De/Para, fallback)

## Critérios de conclusão

- `alembic upgrade head` sem erro
- `\dt public.pc_*` = 0 tabelas retornadas
- `\dt bcu.*` ≥ 11 tabelas
- `SELECT count(*) FROM operacional.propostas WHERE bcu_cabecalho_id IS NOT NULL` = 0 (correto — sem dados em PRD)
- **200+ PASS, 0 FAIL** no pytest
- **0 erros** no `tsc --noEmit`
- Todos os 8 tasks com checkboxes marcados
- `POST /bcu/importar` → 200 + cabecalho criado + base_tcpo sincronizado
- `POST /bcu/de-para` com tipo incoerente → 422; duplicado → 409
- `cpu_custo_service`: insumo mapeado → custo de `bcu.*`; não mapeado → `BaseTcpo.custo_base` + warning no log
- `GET /admin/import/execute?source_type=PC` → 410 Gone
- `BcuDeParaPage` carrega, selects encadeados funcionam, save inline funciona
- Upload `/upload` (admin): seção "Converter" ausente; "BCU" funciona
- Documentos `technical-review` e `walkthrough` criados
- BACKLOG atualizado para TESTED

## Diretório de trabalho (principais)

```
app/alembic/versions/023_bcu_unificada.py
app/backend/models/bcu.py
app/backend/models/proposta.py  (bcu_cabecalho_id)
app/backend/repositories/bcu_repository.py
app/backend/repositories/bcu_de_para_repository.py
app/backend/services/bcu_service.py
app/backend/services/bcu_de_para_service.py
app/backend/services/cpu_custo_service.py
app/backend/services/etl_service.py  (remover parse_converter_datacenter)
app/backend/api/v1/endpoints/bcu.py
app/backend/api/v1/endpoints/admin.py  (deprecar PC + Converter)
app/backend/schemas/bcu.py
app/backend/tests/unit/test_bcu_service.py
app/backend/tests/unit/test_bcu_de_para_service.py
app/backend/tests/unit/test_bcu_endpoints.py
app/backend/tests/unit/test_cpu_custo_service.py  (modificar)
app/frontend/src/shared/services/api/bcuApi.ts
app/frontend/src/shared/services/api/bcuDeParaApi.ts
app/frontend/src/features/bcu/BcuPage.tsx
app/frontend/src/features/bcu/BcuDeParaPage.tsx
app/frontend/src/features/admin/UploadTcpoPage.tsx
app/frontend/src/features/admin/AdminPage.tsx
app/frontend/src/app/router.tsx
app/frontend/src/shared/components/layout/navigationConfig.tsx
```

## Commits esperados (sequência mínima)

1. `feat(f2-10): migration 023 + BCU models replacing pc_tabelas`
2. `feat(f2-10): add BcuService with BCU.xlsx import + base_tcpo sync`
3. `feat(f2-10): add BcuDeParaService for explicit TCPO↔BCU mapping`
4. `feat(f2-10): add /bcu and /bcu/de-para endpoints; deprecate Converter ETL`
5. `refactor(f2-10): cpu_custo_service resolves costs via bcu_de_para`
6. `feat(f2-10): add bcu and bcuDeParaApi clients`
7. `feat(f2-10): add BcuPage, BcuDeParaPage, unify uploads`
8. `docs(f2-10): add technical-review and walkthrough, handoff to QA`
