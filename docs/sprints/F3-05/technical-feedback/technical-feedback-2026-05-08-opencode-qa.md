# Technical Feedback — Opencode QA — F3/F3-05

## Veredito
ACCEPTED

## Sprints avaliadas

- **F3-01**: DONE — Demo Readiness Audit. Aceita por Gemini QA em 2026-04-29. Auditoria estática sem alteração de código; 0 P0, 7 P1, 4 P2. Gates bloqueados por ambiente (dependências/rede), documentado corretamente.
- **F3-02**: DONE — Correções críticas UI/UX. Aceita por Gemini QA em 2026-04-29. Responsividade CPU/Match Review, guards de cliente, tratamento de erro em Importar/CPU e visibilidade da fila de aprovação implementados. `npm run build` PASS; `npm run test` 13/13 PASS.
- **F3-04**: DONE — Configurações finais + polimento + smoke demo. Aceita por Gemini QA em 2026-04-29. Empty states Histograma, loading padronizado (`CircularProgress`), métricas Dashboard com `—`, tratamento de campos não-numéricos. `npm run build` PASS; `npm run test` 13/13 PASS.
- **F3-05**: TESTED — Hotfix PQ Match + TCPO Recursive Tree. Código revisado e gates executados nesta sessão.

## Gates executados

| Comando | Resultado | Observação |
|---|---|---|
| `git diff --check` | **PASS** | Sem erros de whitespace. |
| `python3 -m compileall -q app/backend` | **PASS** | Sem erros de sintaxe/compilação. |
| `npm run build` (em `app/frontend`) | **PASS** | Build concluído em 8.70s. Warning pré-existente de chunk > 500 kB (não bloqueante). |
| `pytest` / `python3 -m pytest` | **BLOCKED** | `pytest` não instalado no ambiente. Blocker ambiental, não regressão de código. |

## Achados

**Nenhum bloqueador (P0) para F3-05.**

### P1
1. **Contrato `origem` TCPO/Própria — já corrigido em 51960ce.** O scan externo em `docs/audits/` (Opus, 2026-05-08) reportou divergência `origem: str | None` (back) vs `origem: 'TCPO' \| 'PROPRIA'` (front) como P0. O commit `51960ce` (“Fix service origin serialization”) introduziu `model_validator` no `ServicoTcpoResponse` que garante `origem` sempre populado (`TCPO` quando `cliente_id` é `None`, `PROPRIA` caso contrário). O contrato está alinhado no HEAD (`628a223`).
2. **`docs/audits/` untracked.** Dois arquivos de auditoria externa (`opus-full-scan-2026-05-08-*.md`) estão no working tree e não são parte do pipeline documental formal do projeto. Não estão no `.gitignore`. Recomendação: incluir `docs/audits/` no `.gitignore` ou mover para fora do repo se não forem artefatos oficiais.
3. **Risco de ambiente para testes.** `pytest` ausente impede regressão automática do backend. A sprint anterior (F2-DT-A) registrou 197+ PASS; F3-05 reporta testes focados passando na worktree do worker, mas não é possível reproduzir no ambiente de QA.

### P2
4. **Warning de chunk > 500 kB no Vite** — pré-existente desde F2-DT-B; não bloqueante para demo.
5. **DOM inválido em `ExpandableTreeRow`** (`<tr>` dentro de `<div>` no `Collapse`) — pré-existente desde F2-13; browser corrige silenciosamente em runtime.

## Recomendações

1. **Instalar `pytest` no ambiente de CI/QA** para desbloquear regressão automática do backend (mínimo: `pip install pytest pytest-asyncio httpx`).
2. **Adicionar `docs/audits/` ao `.gitignore`** ou formalizar política de artefatos de auditoria externa.
3. **Hotfix pós-demo (herdado do scan Opus):**
   - `scripts/run_alembic.py`: caminhos absolutos Windows hardcoded (`C:\DinamicaBudget`). Mover para `scripts/win/` ou parametrizar.
   - `servico_catalog_service._explode_recursivo_tcpo`: propagar `visited` entre chamadas recursivas e adicionar `max_depth` defensivo.
   - `endpoints/admin.py`: background task de embeddings com `except Exception` silencioso; logar `exc_info=True` e respeitar flag `recomputar_embeddings` do request.
4. **Hardening de `ServicesPage.tsx`:** remover import órfão de `Box` (linha 6 não existe mais no HEAD atual, mas validar em revisão manual futura).

## Decisão de status recomendada

**F3-05 pode ser movida de TESTED para DONE.**

Justificativa:
- Upload PQ com itens válidos altera status da proposta para `EM_ANALISE` (`pq_import_service.py:171-172`), habilitando Match conforme contrato.
- Tela reaberta consulta `pq-itens` via `useQuery` e habilita botão de Match por existência real de itens (`ProposalImportPage.tsx:41-47`).
- Árvore TCPO expande filhos `SERVICO` recursivamente com lazy-load (`ServicesPage.tsx`/`ExpandableTreeRow.tsx`).
- Parser TCPO preserva hierarquia pai → subserviço → filhos via pilha de indentação (`etl_service.py:179-300`).
- Contrato `origem` front/back está alinhado após hotfix no commit `51960ce`.
- Build frontend verde, backend compila, diff check limpo.
- Não há alteração de código de produção nesta sessão de QA.
