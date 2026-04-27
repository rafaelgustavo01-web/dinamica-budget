# Sprint F2-09 — Briefing

**Sprint:** F2-09
**Titulo:** Versionamento de Propostas + Workflow de Aprovação
**Worker:** claude-sonnet-4-6
**Status:** BACKLOG → INICIADA
**Data:** 2026-04-27
**Prioridade:** P1

---

## Contexto

F2-08 DONE (158 PASS, QA Amazon Q aprovado). Dependência liberada.

Esta sprint fecha o Milestone 6 (Proposta Completa). Adiciona:
1. **Versionamento**: cada proposta pode gerar múltiplas versões (`proposta_root_id` como agrupador lógico). Nova versão clona metadados, fecha a anterior, começa limpa (RASCUNHO).
2. **Workflow de aprovação**: proposta com `requer_aprovacao=True` passa pelo fluxo `CPU_GERADA → AGUARDANDO_APROVACAO → APROVADA`. Rejeição volta para `CPU_GERADA`.

## Objetivo

- Migration 022: adicionar 8 campos de versioning/aprovação + enum value `AGUARDANDO_APROVACAO`
- `require_proposta_role` atualizado para resolver ACL via `proposta_root_id` (versões herdam permissões da raiz)
- `PropostaVersionamentoService`: `nova_versao`, `enviar_aprovacao`, `aprovar`, `rejeitar`, `listar_versoes`
- 5 endpoints + rota fila de aprovações
- Frontend: `ProposalHistoryPanel` + `ApprovalQueuePage` + botões condicionais no detail

## Decisões de produto (NÃO rediscutir)

| Decisão | Valor |
|---|---|
| `nova_versao` clona PQ/CPU? | **NÃO** — versão nova começa limpa (RASCUNHO) |
| Rejeitar → qual status? | **CPU_GERADA** (volta editável, CPU preservada) |
| Quem pode enviar para aprovação? | **EDITOR ou OWNER** |
| Quem pode aprovar/rejeitar? | **APROVADOR ou OWNER** |
| Workflow obrigatório? | **NÃO** — flag `requer_aprovacao` por proposta |
| proposta_acl por versão ou root? | **root** — versões herdam da raiz automaticamente |

## Critérios de Aceite

- Migration 022 aplicada sem erro; `SELECT count(*) FROM propostas WHERE proposta_root_id IS NULL` = 0
- `require_proposta_role` usa `proposta_root_id` para resolver ACL — regressão F2-08 100% pass
- `nova_versao`: nova proposta com `numero_versao = atual+1`, anterior com `is_versao_atual=FALSE`, `is_fechada=TRUE`
- `enviar_aprovacao`: requer `requer_aprovacao=True` + `status=CPU_GERADA` → `AGUARDANDO_APROVACAO`
- `aprovar`: requer APROVADOR+, status `AGUARDANDO_APROVACAO` → `APROVADA`
- `rejeitar`: requer APROVADOR+, status `AGUARDANDO_APROVACAO` → `CPU_GERADA`
- Rota `/aprovacoes` retorna propostas aguardando aprovação onde user é APROVADOR/OWNER
- `ProposalHistoryPanel` exibe lista de versões agrupadas por root
- `ApprovalQueuePage` com ações aprovar/rejeitar inline
- Botões condicionais no detail: "Nova Versão" (EDITOR+), "Enviar Aprovação" (EDITOR+, quando cabe), "Aprovar"/"Rejeitar" (APROVADOR+, quando aguardando)
- Badge AGUARDANDO_APROVACAO na UI com cor amber
- **170+ pytest PASS, 0 FAIL**
- **0 erros `npx tsc --noEmit`**

## Plano

Arquivo: `docs/sprints/F2-09/plans/2026-04-27-versionamento-aprovacao.md`

7 tasks:
1. Migration 022 + model (autocommit_block para ALTER TYPE)
2. `require_proposta_role` → resolve via root_id
3. `PropostaVersionamentoService` + repo methods + testes
4. Schemas + 5 endpoints novos (atenção à ordem de registro)
5. Frontend API client (append ao final de proposalsApi.ts)
6. UI: ProposalHistoryPanel + ApprovalQueuePage + ProposalDetailPage
7. Validação final + walkthrough + technical-review + BACKLOG TESTED

## Pré-requisito de leitura (CRÍTICO)

1. `docs/sprints/F2-08/technical-review/technical-review-2026-04-26-f2-08.md`
2. `app/backend/models/proposta.py` — campos atuais
3. `app/backend/models/enums.py` — StatusProposta, PropostaPapel
4. `app/backend/core/dependencies.py` — require_proposta_role atual
5. `app/backend/api/v1/endpoints/propostas.py` — padrão pós F2-08
6. `app/backend/services/proposta_service.py`
7. `app/alembic/versions/021_proposta_acl.py` — padrão de migration
8. `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx`
9. `app/frontend/src/features/proposals/routes.tsx`

## Atenções especiais (claude-sonnet)

- **`ALTER TYPE ... ADD VALUE` EXIGE `autocommit_block`** — o PostgreSQL não aceita esse DDL dentro de uma transação. Usar `with op.get_context().autocommit_block(): op.execute(...)`. Sem isso a migration falha.
- **Ordem de rotas importa**: `/aprovacoes` e `/root/{root_id}/versoes` devem ser declaradas ANTES de `/{proposta_id}` no router Python (FastAPI resolve por ordem). No frontend, rota `aprovacoes` antes de `:id` nas rotas React.
- **`require_proposta_role` retrocompatível**: `proposta_root_id = id` para todas as propostas existentes após backfill. A mudança preserva 100% o comportamento de F2-08.
- **Código de nova versão**: `codigo = f"{atual.codigo.split('-v')[0]}-v{proximo_numero}"` — garante que a versão 3 de "ORC-001-v2" vira "ORC-001-v3", não "ORC-001-v2-v3".
- **`PropostaResponse` retrocompatível**: adicionar campos novos como `Optional` / `None` para não quebrar testes existentes de F2-01..F2-08.
- **Append em proposalsApi.ts**: adicionar métodos no FINAL, sem reescrever blocos existentes de F2-06/F2-07/F2-08.
- **Testes com 170+ PASS**: a sprint adiciona ~16 novos testes sobre os 158 existentes. Não mudar testes existentes.
- **Frontend UX suave**: `ApprovalQueuePage` deve funcionar mesmo com lista vazia (estado empty state adequado).

## Dependências

- F2-08 DONE ✅ (proposta_acl, require_proposta_role, PropostaPapel.APROVADOR)
- F2-04 DONE ✅ (CPU existe para poder enviar aprovação com status CPU_GERADA)
