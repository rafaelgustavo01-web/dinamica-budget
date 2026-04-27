# Worker Prompt — Sprint F2-09

**Para:** Claude Sonnet 4.6 (claude-sonnet-4-6)
**Modo:** Agent / BUILD
**Sprint:** F2-09 — Versionamento de Propostas + Workflow de Aprovação
**Repo:** C:\Users\rafae\Documents\workspace\github\dinamica-budget
**Prioridade:** P1 — fecha Milestone 6

---

Você é o worker da Sprint F2-09. Implemente o plano completo em `docs/sprints/F2-09/plans/2026-04-27-versionamento-aprovacao.md` do início ao fim sem pausas.

## Por que você foi escolhido

Esta sprint tem **forte componente de frontend + workflow de estado**, com backend moderado:

- UI complexa: 2 novas páginas (ProposalHistoryPanel + ApprovalQueuePage) + múltiplos botões condicionais com lógica de papel e status
- Máquina de estados: RASCUNHO → CPU_GERADA → AGUARDANDO_APROVACAO → APROVADA/CPU_GERADA — requer atenção a edge cases de UX
- Backend enxuto: 1 service + 5 endpoints + migration (sem refactor de serviços complexos)
- Retrocompatibilidade crítica: F2-08 entregou 158 testes — não quebrar nenhum

## Instruções de execução

1. **OBRIGATÓRIO antes de codar**: leia em ordem os 9 documentos/arquivos listados em "Pré-requisito de leitura" no briefing
2. Leia o briefing: `docs/sprints/F2-09/briefing/sprint-F2-09-briefing.md`
3. Leia o plano: `docs/sprints/F2-09/plans/2026-04-27-versionamento-aprovacao.md`
4. Execute cada task em ordem, commitando após cada uma
5. Após cada task de backend: `cd app && python -m pytest backend/tests/ -v --tb=short`
6. Após cada task de frontend: `cd app/frontend && npx tsc --noEmit`
7. Ao concluir TODAS as tasks:
   - Crie `docs/sprints/F2-09/technical-review/technical-review-2026-04-27-f2-09.md`
   - Crie `docs/sprints/F2-09/walkthrough/done/walkthrough-F2-09.md`
   - Atualize F2-09 para **TESTED** em `docs/shared/governance/BACKLOG.md`

## Atenções especiais

- **`ALTER TYPE ... ADD VALUE` EXIGE `autocommit_block`**:
  ```python
  with op.get_context().autocommit_block():
      op.execute("ALTER TYPE operacional.status_proposta_enum ADD VALUE IF NOT EXISTS 'AGUARDANDO_APROVACAO'")
  ```
  Sem isso a migration falhará com `ALTER TYPE ... cannot run inside a transaction block`.

- **Ordem de rotas no router Python**: declarar `/aprovacoes` e `/root/{root_id}/versoes` ANTES de `/{proposta_id}`. FastAPI avalia rotas na ordem de registro — se `/{proposta_id}` vier primeiro, a string "aprovacoes" será capturada como UUID e retornará 422.

- **Ordem de rotas no React**: em `routes.tsx`, a rota `aprovacoes` deve vir antes de `:id` pelo mesmo motivo.

- **`require_proposta_role` retrocompatível**: o backfill da migration garante `proposta_root_id = id` para todas as propostas existentes. A mudança no dependency apenas adiciona uma linha de leitura do campo — comportamento idêntico ao de F2-08 para dados existentes.

- **Código da nova versão**: use `atual.codigo.split('-v')[0]` para extrair o código base antes de adicionar o sufixo `-v{N}`. Garante que "ORC-001-v2" gera "ORC-001-v3", não "ORC-001-v2-v3".

- **`PropostaResponse` retrocompatível**: todos os campos novos devem ser `Optional` com `default=None` para não quebrar os 158 testes existentes que serializam `PropostaResponse` sem esses campos.

- **`proposta_root_id` nullable no model**: colunas novas são nullable no DDL (Alembic não suporta ADD COLUMN NOT NULL sem default no PostgreSQL lock-free). O backfill garante que estejam preenchidas. Para novos registros, o service popula no momento de criação.

- **`nova_versao` popula `proposta_root_id`** no novo registro: `proposta_root_id = atual.proposta_root_id` (não `atual.id` — seria incorreto para versões 3+).

- **Append em `proposalsApi.ts`**: adicionar tipos e métodos no FINAL do arquivo, sem reescrever blocos de F2-06/F2-07/F2-08.

- **ApprovalQueuePage**: implementar empty state adequado ("Nenhuma proposta aguardando aprovação") — não deixar lista vazia sem feedback visual.

- **Badge AGUARDANDO_APROVACAO**: usar cor `warning` (amber) do MUI, consistente com os outros status badges da aplicação. Verificar como outros status (RASCUNHO, CPU_GERADA, APROVADA) estão estilizados em `ProposalDetailPage` antes de implementar.

## Critérios de conclusão

- Migration 022 aplicada sem erro (autocommit_block correto)
- `SELECT count(*) FROM operacional.propostas WHERE proposta_root_id IS NULL` = 0 (backfill OK)
- **170+ PASS, 0 FAIL** no pytest (regressão F2-08 intacta)
- **0 erros** no `tsc --noEmit`
- Todos os 7 tasks com checkbox marcado
- `nova_versao` retorna 201 com `numero_versao` incrementado, versão anterior com `is_versao_atual=FALSE`
- Workflow de aprovação funcional (enviar → aprovar/rejeitar → status correto)
- `GET /aprovacoes` filtra por papel do usuário
- `ProposalHistoryPanel` renderiza lista de versões com link para cada uma
- `ApprovalQueuePage` com ações aprovar/rejeitar + empty state
- Botões condicionais corretos no `ProposalDetailPage`
- Documentos technical-review e walkthrough criados
- BACKLOG atualizado para TESTED

## Diretório de trabalho

```
app/backend/models/enums.py
app/backend/models/proposta.py
app/alembic/versions/022_proposta_versionamento.py
app/backend/core/dependencies.py
app/backend/services/proposta_versionamento_service.py
app/backend/repositories/proposta_repository.py
app/backend/schemas/proposta.py
app/backend/api/v1/endpoints/propostas.py
app/backend/tests/unit/test_proposta_versionamento_service.py
app/backend/tests/unit/test_proposta_versionamento_endpoints.py
app/frontend/src/shared/services/api/proposalsApi.ts
app/frontend/src/features/proposals/components/ProposalHistoryPanel.tsx
app/frontend/src/features/proposals/pages/ApprovalQueuePage.tsx
app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx
app/frontend/src/features/proposals/routes.tsx
```

## Commits esperados (sequência mínima)

1. `feat(f2-09): add versioning and approval fields to Proposta model + migration 022`
2. `refactor(f2-09): require_proposta_role resolves ACL via proposta_root_id`
3. `feat(f2-09): add PropostaVersionamentoService with nova_versao and approval workflow`
4. `feat(f2-09): add versioning and approval endpoints`
5. `feat(f2-09): add versioning/approval API client methods`
6. `feat(f2-09): add ProposalHistoryPanel, ApprovalQueuePage and conditional approval UI`
7. `docs(f2-09): add technical-review and walkthrough, handoff to QA`
