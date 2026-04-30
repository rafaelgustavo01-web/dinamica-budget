# Technical Feedback — Sprint F2-10 (QA)

**Data:** 2026-04-29
**QA:** Claude Code (claude-sonnet-4-6)
**Sprint:** F2-10 — BCU Unificada + De/Para
**Veredicto:** ✅ APROVADA — DONE (com hotfixes aplicados)

---

## Suite de Testes

| Conjunto | Resultado |
|---|---|
| `python -m pytest backend/tests/ -q` | **223 PASS, 0 FAIL** |
| Testes BCU (`-k bcu`) | **14 PASS** |
| `npm run test` (vitest) | **13 PASS** |
| `tsc --noEmit` | **0 erros** |
| `npm run build` | **✓** |

## Critérios de Aceite Verificados

| Criterio | Status |
|---|---|
| Migration 023 (drop pc_*, create schema bcu.* + de_para) | ✅ `alembic/versions/023_bcu_unificada.py` |
| `BcuService.importar_bcu` + sync `referencia.base_tcpo` (codigo_origem) | ✅ `bcu_service.py` |
| `BcuDeParaService` CRUD + validacao tipo coerente | ✅ `bcu_de_para_service.py` |
| UI: BcuPage + BcuDeParaPage | ✅ `features/admin/` |
| Uploads unificados em `UploadTcpoPage` | ✅ TCPO + BCU em um unico formulario |
| `cpu_custo_service` usa De/Para com fallback `BaseTcpo` | ✅ |
| Branch main | ✅ |

## Hotfixes Identificados e Corrigidos Durante QA (2026-04-29)

### H-01 — `importar_converter` endpoint: excecoes nao capturadas
- **Causa:** catch apenas `(IndexError, KeyError, AttributeError)`; excecoes SQLAlchemy escapavam causando drop de conexao (Axios "Network Error")
- **Fix:** adicionado broad `except Exception` com `await db.rollback()` + mensagem estruturada; `ValueError` adicionado ao catch narrow
- **Commit:** `4ab9164`

### H-02 — Novo endpoint `POST /bcu/importar-converter` para Converter em Data Center.xlsx
- **Causa:** `BcuService.importar_converter()` implementado mas nao havia endpoint dedicado; frontend chamava `/bcu/importar` (parser legado) com o Converter file, causando `IndexError` no `_parse_equipamentos` (espera 12 colunas; Converter tem 6)
- **Fix:** endpoint `POST /bcu/importar-converter` ja estava implementado no commit BCU (`a42ca7c`); `bcuApi.importarPlanilha` ja apontava para o novo endpoint
- **Status:** ja corrigido em sprint anterior; hotfix H-01 torna o erro visivel em vez de silencioso

## Notas

- `BcuService.importar_converter()` parse inline funciona corretamente: 170 linhas em 5 abas (MO=50, EQP=30, ENCARGOS=45, EPI=17, FER=28); EXAMES registrado como aviso no cabecalho.
- `_parse_equipamentos` (legado, usada por `importar_bcu`) nao serve para o Converter; a separacao de parsers e correta arquiteturalmente.

## Conclusao

Migration 023 aplicada, schema bcu.* funcional, De/Para CRUD com validacao, cpu_custo_service refatorado.
Hotfixes de robustez no endpoint aplicados. Suite verde. **DONE**.
