# Technical Feedback — Sprint F2-DT-A (QA)

**Data:** 2026-04-29
**QA:** Claude Code (claude-sonnet-4-6)
**Sprint:** F2-DT-A — Backend Tech Debt Cleanup
**Veredicto:** ✅ APROVADA — DONE

---

## Suite de Testes

| Conjunto | Resultado |
|---|---|
| `python -m pytest backend/tests/ -x -q` | **223 PASS, 0 FAIL** |
| Warnings | 9 (deprecation/cache — nao bloqueiam) |

## Critérios de Aceite Verificados

| Criterio | Status |
|---|---|
| 4 commits atomicos `feat(f2-dt-a/N)` | ✅ commits `8e40517`, `88dcdee`, `c747961`, `dde6353` + QA fix `93919e1` |
| pytest infra resiliente (Windows loop, dotenv, schemas, ENUMs) | ✅ conftest.py sem WindowsSelectorEventLoopPolicy errors |
| Purga pipeline legado (subprocess + import_preview_service + dead endpoints) | ✅ `import_preview_service.py` removido; endpoints `/admin/import/preview` e `/admin/import/execute` removidos |
| N+1 batch em 5 services (histograma, catalogo, versionamento) | ✅ queries em lote; `perf(f2-dt-a/3)` commit |
| ETL durabilidade via `operacional.etl_preview` | ✅ migration 025; EtlService DB-first lookup + `_cache` fallback |
| `codigo_origem` em `ComposicaoComponenteResponse` | ✅ schema + endpoint retornam o campo |
| Branch main apenas | ✅ |

## Itens QA Corrigidos (post-TESTED)

| ID | Severidade | Descricao | Status |
|---|---|---|---|
| A-04 | Medium | BytesIO leak em `proposta_export_service.py` | ✅ corrigido no commit `93919e1` |
| M-03 | Medium | Bug `capa["B2"] = proposta.codigo` vs `cliente.nome_fantasia` | ✅ corrigido |
| M-06 | Low | 8 imports locais em `nova_versao` body | ✅ promovidos para modulo |

## Hotfixes Adicionais (pos-QA, 2026-04-29)

- `fix(upload)`: `etl_service._parse_tcpo_pini_result` usava `read_only=True` que remove formatacao de celulas, zerando deteccao de servicos-pai. Corrigido para `read_only=False`. Commit `4ab9164`.
- `fix(upload)`: `bcu.importar_converter` endpoint so capturava `IndexError|KeyError|AttributeError`; excecoes SQLAlchemy escapavam causando "Network Error" no cliente. Adicionado broad `except Exception` com rollback explicito. Commit `4ab9164`.

## Conclusao

Sprint F2-DT-A entregou todos os 18 itens de divida tecnica conforme checkpoint 2026-04-27.
Suite verde, build limpo, hotfixes aplicados. **DONE**.
