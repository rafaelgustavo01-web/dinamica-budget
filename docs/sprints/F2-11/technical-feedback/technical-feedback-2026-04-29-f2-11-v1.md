# Technical Feedback — Sprint F2-11 (QA)

**Data:** 2026-04-29
**QA:** Claude Code (claude-sonnet-4-6)
**Sprint:** F2-11 — Histograma da Proposta
**Veredicto:** ✅ APROVADA — DONE

---

## Suite de Testes

| Conjunto | Resultado |
|---|---|
| `python -m pytest backend/tests/ -q` | **223 PASS, 0 FAIL** |
| Testes histograma (`-k histograma`) | **7 PASS** |
| `npm run test` (vitest) | **13 PASS** — ProposalHistogramaPage smoke test incluso |
| `tsc --noEmit` | **0 erros** |
| `npm run build` | **✓** |

## Critérios de Aceite Verificados

| Criterio | Status |
|---|---|
| Migration 024 (tabelas `proposta_pc_*` + recurso_extra + alocacao + flag `cpu_desatualizada`) | ✅ `alembic/versions/024_proposta_histograma.py` |
| `HistogramaService.montar_histograma` | ✅ `histograma_service.py` |
| `ProposalHistogramaPage` com abas editaveis | ✅ `features/proposals/pages/ProposalHistogramaPage.tsx` |
| Divergencia BCU detectada e exibida | ✅ chip "divergencias" no UI |
| `nova_versao` clona histograma | ✅ `proposta_versionamento_service.py` |
| `cpu_custo_service` hierarquia `proposta_pc > bcu > BaseTcpo` | ✅ |
| Smoke test `ProposalHistogramaPage.test.tsx` — 4 asserts | ✅ via F2-DT-C (render, abas, divergencia, edicao inline) |
| Branch main | ✅ |

## Notas

- Dependencia de F2-10 (BCU) confirmada satisfeita: schema `bcu.*` disponivel, sync `referencia.base_tcpo` funcional.
- Recursos extras alocaveis e `AlocacaoRecursoDialog` implementados conforme spec.

## Conclusao

Histograma snapshot editavel por proposta, 7 abas, divergencia BCU, recursos extras, clone na nova versao.
Suite verde. Smoke test coberto. **DONE**.
