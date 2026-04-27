# Sprint F2-10 — Briefing

**Sprint:** F2-10
**Titulo:** BCU Unificada (Base de Custos Unitários) + De/Para
**Worker:** kimi-k2.6
**Status:** PLAN → TODO
**Data:** 2026-04-27
**Prioridade:** P1

---

## Contexto

F2-09 DONE (179 PASS, 0 tsc, QA pendente). Dependência liberada.

Esta sprint inicia o Milestone 7 (BCU + Histograma). O banco de dados tem três pipelines sobrepostos que fazem a mesma coisa: `pc_tabelas_service.importar_pc_tabelas`, `etl_service.parse_converter_datacenter` e a "Carga inteligente PC". Os três populam tabelas relacionadas a custos unitários mas são tratados como recursos separados.

**Decisão arquitetural aprovada pelo PO (2026-04-27):** unificar tudo em um único schema `bcu.*` com uma única tela de importação e uma tabela de mapeamento explícito **De/Para** entre o catálogo `referencia.base_tcpo` e os itens de custo da BCU.

O banco **pode ser resetado**: o PO autorizou drop direto de `pc_*` sem backfill de dados (ainda não há dados em PRD).

## Objetivo

1. **Migration 023**: drop `public.pc_*` + `etl_carga`; create schema `bcu` com 10 tabelas + `bcu.de_para`; add `propostas.bcu_cabecalho_id`
2. **BcuService**: importar `BCU.xlsx` (7 abas) → popula `bcu.*` E sincroniza `referencia.base_tcpo` com `codigo_origem` derivado
3. **BcuDeParaService**: CRUD 1:1 entre `referencia.base_tcpo` e `bcu.*` com validação de tipo coerente
4. **Endpoints `/bcu/*`**: 9 GET/POST/PATCH/DELETE + 4 endpoints De/Para
5. **Refatorar `cpu_custo_service`**: lookup via `bcu_de_para` → `bcu.*`; fallback `BaseTcpo.custo_base` com warning
6. **Frontend**: `BcuPage` (rebrand PcTabelasPage) + `BcuDeParaPage` (nova) + uploads unificados + nav atualizado

## Decisões de produto (NÃO rediscutir)

| Decisão | Valor |
|---|---|
| Nome da base global | **BCU — Base de Custos Unitários** |
| Schema PostgreSQL | **`bcu.*`** (paralelo a `referencia.*` e `operacional.*`) |
| Reset do banco | **Autorizado** — drop direto, sem backfill de pc_* |
| De/Para | **Manual 1:1** — UniqueConstraint em `base_tcpo_id` |
| Encargos/Mobilização no De/Para | **NÃO** — são globais, não mapeáveis (entram direto no histograma em F2-11) |
| Múltiplas versões BCU | **SIM** — `bcu.cabecalho` com `is_ativo` flag (índice parcial garante 1 ativo) |
| Sync BCU → base_tcpo | **SIM** — importação cria/atualiza `BaseTcpo` com `codigo_origem = "BCU-{tipo}-{N}"` |
| cpu_custo_service fallback | **`BaseTcpo.custo_base`** com warning estruturado quando sem mapeamento |

## Critérios de Aceite

- Migration 023 aplicada sem erro; `\dt public.pc_*` = 0 tabelas; `\dt bcu.*` ≥ 11 tabelas
- `POST /bcu/importar` cria cabecalho + popula todas as abas + cria/atualiza BaseTcpo correspondentes
- `POST /bcu/cabecalhos/{id}/ativar` desativa anteriores; `GET /bcu/cabecalho-ativo` retorna o ativo
- `POST /bcu/de-para` com tipo incoerente → 422; duplicado `base_tcpo_id` → 409
- `cpu_custo_service`: insumo com De/Para → custo de `bcu.*`; sem De/Para → `BaseTcpo.custo_base` + log warning
- `GET /admin/import/execute?source_type=PC` → 410 Gone
- `BcuDeParaPage`: tabela paginada com 2 selects encadeados (tipo → item), save inline, badge de cobertura
- Upload em `/upload` (admin): seção "Converter" removida; seção "BCU" funcional
- `AdminPage`: dropdown "Carga inteligente" só mostra "TCPO"
- **200+ pytest PASS, 0 FAIL**
- **0 erros `npx tsc --noEmit`**

## Plano

Arquivo: `docs/sprints/F2-10/plans/2026-04-27-bcu-unificada-de-para.md`

8 tasks:
1. Migration 023 + models BCU
2. `BcuService` (importação + sync base_tcpo)
3. `BcuDeParaService` (CRUD + validação tipo coerente)
4. Endpoints `/bcu/*` + `/bcu/de-para` + deprecar PC no admin
5. Refatorar `cpu_custo_service` (lookup De/Para + fallback)
6. Frontend API clients (`bcuApi.ts`, `bcuDeParaApi.ts`)
7. Frontend UI (BcuPage, BcuDeParaPage, UploadTcpoPage, AdminPage, router, nav)
8. Validação final + walkthrough + technical-review + BACKLOG TESTED

## Pré-requisito de leitura (CRÍTICO — nesta ordem)

1. `docs/shared/governance/BACKLOG.md` — sprint F2-10 (escopo + critérios de aceite)
2. `docs/sprints/F2-09/technical-review/technical-review-2026-04-27-f2-09.md`
3. `app/backend/models/pc_tabelas.py` — estrutura atual a substituir
4. `app/backend/services/pc_tabelas_service.py` — parser a reusar em bcu_service
5. `app/backend/services/etl_service.py` — `parse_converter_datacenter` a remover
6. `app/backend/services/cpu_custo_service.py` — lookup atual (a refatorar)
7. `app/backend/api/v1/endpoints/pc_tabelas.py` — endpoints atuais
8. `app/backend/api/v1/endpoints/admin.py` — seções a remover
9. `app/backend/models/base_tcpo.py` — alvo do De/Para
10. `app/alembic/versions/022_proposta_versionamento.py` — padrão de migration
11. `app/frontend/src/features/pc-tabelas/PcTabelasPage.tsx` — UI a renomear
12. `app/frontend/src/features/admin/UploadTcpoPage.tsx` — seções a unificar
13. `app/frontend/src/shared/services/api/pcTabelasApi.ts` — API client a renomear

## Atenções especiais (Kimi K2.6)

- **FK polimórfica**: `bcu.de_para.bcu_item_id` NÃO tem FK física no banco (aponta para 5 tabelas diferentes). A integridade referencial é garantida inteiramente no service (`BcuDeParaService.criar` valida que o UUID existe na tabela correta).
- **Índice parcial UNIQUE em `is_ativo`**: `CREATE UNIQUE INDEX ix_bcu_cabecalho_ativo ON bcu.cabecalho (is_ativo) WHERE is_ativo = TRUE`. Isso garante no máximo 1 ativo. O service também deve desativar todos antes de ativar o novo.
- **Re-importação idempotente**: o `BcuService` deve fazer UPSERT por `codigo_origem` — se o código já existe, atualiza os valores; não cria duplicata. Mesmo comportamento em `referencia.base_tcpo`.
- **`codigo_origem` derivado**: `BCU-MO-001`, `BCU-EQP-001`, `BCU-EPI-001`, `BCU-FER-001` (0-padded com 3 dígitos, sequencial por tipo na planilha). Encargos e Mobilização NÃO geram `codigo_origem`.
- **Tipo coerente De/Para**: `MO TCPO → MO BCU`; `EQUIPAMENTO TCPO → EQP BCU`; `INSUMO TCPO → EPI ou FER BCU`; `FERRAMENTA TCPO → FER BCU`. Qualquer outro combinação → 422 com mensagem clara.
- **`pc_cabecalho_id` → `bcu_cabecalho_id`**: renomear em todo o backend e frontend (ripgrep: `pc_cabecalho_id`). Arquivos esperados: `cpu_geracao_service.py`, `proposta_repository.py`, `schemas/proposta.py`, `proposalsApi.ts`.
- **Ordem de rotas em FastAPI**: `/bcu/de-para` e `/bcu/cabecalho-ativo` devem ser declarados ANTES de `/bcu/{cabecalho_id}/...` para não capturar "de-para" como UUID.
- **Testes 200+ PASS**: base é 179 de F2-09. Adicionar ~25 testes novos (10 bcu_service + 8 de_para_service + 12 endpoints + 5 cpu_custo_service). Não alterar testes existentes.
- **Deletar com segurança**: `pc_tabelas.py`, `pc_tabelas_service.py`, `pc_tabelas_repository.py`, `pc_tabelas.py` (schema), `PcTabelasPage.tsx`, `pcTabelasApi.ts`, `pc_tabelas.py` (endpoint). Confirmar que nenhum import quebrou antes de deletar.

## Dependências

- F2-09 TESTED ✅ (versionamento + aprovação entregues; QA em andamento — não bloqueia)
- F2-08 DONE ✅ (RBAC por proposta, `proposta_acl` pronto)
