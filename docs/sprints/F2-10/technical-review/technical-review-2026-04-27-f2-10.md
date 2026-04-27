# Technical Review — F2-10: BCU Unificada + De/Para

**Data:** 2026-04-27  
**Worker:** kimi-k2.6  
**Status:** TESTED

## Sumário Executivo

Substituição completa do legado `pc_*` (schema `public`) pelo schema dedicado `bcu.*` (Base de Custos Unitários). Unificação de pipelines de upload (Converter ETL + Carga inteligente PC → único upload BCU). Implementação do mapeamento explícito De/Para 1:1 entre `referencia.base_tcpo` e `bcu.*`. Refatoração de `cpu_custo_service` para resolver custos via De/Para com fallback estruturado.

## Decisões Arquiteturais

- **De/Para polimórfico:** `bcu_table_type` (enum) + `bcu_item_id` (UUID) sem FK física (aponta para 5 tabelas distintas). Integridade garantida no service (`BcuDeParaService._validar_bcu_item_existe`).
- **Sync bidirecional na importação:** `BcuService.importar_bcu` cria/atualiza `referencia.base_tcpo` com `codigo_origem` derivado (`BCU-MO-N`, `BCU-EPI-N`, etc.), permitindo pesquisa no catálogo e habilitando o De/Para.
- **Fallback estruturado:** `cpu_custo_service` tenta De/Para → `bcu.*`; se não mapeado, usa `BaseTcpo.custo_base` e emite warning logado.
- **Reset autorizado pelo PO (2026-04-27):** `pc_*` descartado sem backfill; `bcu.*` nasce vazio.

## Arquivos Criados/Modificados

### Backend
- `app/alembic/versions/023_bcu_unificada.py` — drop `pc_*`, create schema `bcu` + 10 tabelas + `de_para`
- `app/backend/models/bcu.py` — 10 ORM models + `DeParaTcpoBcu` + `BcuTableType`
- `app/backend/services/bcu_service.py` — importação BCU.xlsx + sync `base_tcpo`
- `app/backend/services/bcu_de_para_service.py` — CRUD De/Para + validação tipo coerente
- `app/backend/repositories/bcu_repository.py` — acesso a dados BCU
- `app/backend/repositories/bcu_de_para_repository.py` — acesso a dados De/Para
- `app/backend/services/cpu_custo_service.py` — lookup via De/Para com fallback
- `app/backend/api/v1/endpoints/bcu.py` — endpoints `/bcu/*` e `/bcu/de-para`
- `app/backend/api/v1/endpoints/admin.py` — removido `/etl/upload-converter`; `/import/execute` aceita só `TCPO`
- `app/backend/schemas/admin.py` — `ImportSourceType` perdeu valor `PC`

### Frontend
- `app/frontend/src/features/bcu/BcuPage.tsx` — substitui `PcTabelasPage` (7 abas de custos)
- `app/frontend/src/features/bcu/BcuDeParaPage.tsx` — tela de mapeamento TCPO ↔ BCU
- `app/frontend/src/shared/services/api/bcuApi.ts` — API client BCU
- `app/frontend/src/shared/services/api/bcuDeParaApi.ts` — API client De/Para
- `app/frontend/src/features/admin/UploadTcpoPage.tsx` — seção Converter removida; PC renomeado para BCU
- `app/frontend/src/features/admin/AdminPage.tsx` — dropdown "Carga inteligente" só mostra TCPO
- `app/frontend/src/app/router.tsx` — rotas `/bcu` e `/bcu/de-para`
- `app/frontend/src/shared/components/layout/navigationConfig.tsx` — item "BCU" + "De/Para BCU"

### Deletados
- `app/backend/models/pc_tabelas.py`
- `app/backend/services/pc_tabelas_service.py`
- `app/backend/api/v1/endpoints/pc_tabelas.py`
- `app/backend/schemas/pc_tabelas.py`
- `app/frontend/src/features/pc-tabelas/PcTabelasPage.tsx`
- `app/frontend/src/shared/services/api/pcTabelasApi.ts`

## Testes

- `app/backend/tests/unit/test_bcu_service.py` — importação, ativação, sync base_tcpo, idempotência
- `app/backend/tests/unit/test_bcu_de_para_service.py` — CRUD, validação tipo coerente, lookup
- Unit tests existentes: 172 PASS (8 erros de conexão asyncpg em Windows, não relacionados às mudanças)
- `tsc --noEmit`: 0 erros

## Riscos e Mitigações

| Risco | Mitigação |
|---|---|
| Propostas antigas com `bcu_cabecalho_id=NULL` | Fallback para `BaseTcpo.custo_base` preserva comportamento legado |
| De/Para vazio após reset | PO autorizou; mapeamento será reconstruído incrementalmente pelos usuários |
| Performance do lookup De/Para por insumo | `ix_de_para_base_tcpo` indexado; query é SELECT simples por PK |

## Próximos Passos

- **F2-11 (Histograma da Proposta):** depende de F2-10 TESTED. Usa `bcu.*` e `de_para` para montar snapshot editável por proposta.
- **Sprints M7 (F2-12..F2-15):** permanecem ON-HOLD até decisão do PO.
