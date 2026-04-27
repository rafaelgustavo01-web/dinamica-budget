# Walkthrough — Sprint F2-09

**Sprint:** F2-09 — Versionamento de Propostas + Workflow de Aprovação
**Data:** 2026-04-27
**Status:** DONE ✅

---

## Fluxo completo implementado

### 1. Versionamento de Propostas

```
Proposta v1 (ORC-001) — CPU_GERADA
  │
  └─► POST /propostas/{id}/nova-versao
        │
        ├─ v1: is_versao_atual=FALSE, is_fechada=TRUE
        └─ v2: ORC-001-v2, RASCUNHO, is_versao_atual=TRUE
                │
                └─► POST /propostas/{id}/nova-versao
                      ├─ v2: fechada
                      └─ v3: ORC-001-v3, RASCUNHO
```

**Regras:**
- Só a versão atual (`is_versao_atual=TRUE`) pode gerar nova versão
- Uma versão fechada (`is_fechada=TRUE`) não pode gerar nova versão
- Código: `{base}-v{N}` — extrai base antes do primeiro `-v` para evitar sufixação dupla
- `proposta_root_id` é o agrupador lógico (imutável, aponta para a primeira versão)
- ACL é sempre resolvida pelo `proposta_root_id` — versões herdam permissões da raiz

### 2. Workflow de Aprovação

```
requer_aprovacao = True
         │
         ▼
    CPU_GERADA
         │
         └─► POST /propostas/{id}/enviar-aprovacao (EDITOR+)
                       │
                       ▼
              AGUARDANDO_APROVACAO (badge amber)
                       │
              ┌─────────┴─────────┐
              ▼                   ▼
     POST /aprovar             POST /rejeitar
     (APROVADOR+)              (APROVADOR+)
              │                   │
              ▼                   ▼
          APROVADA            CPU_GERADA
                         (motivo_revisao salvo)
```

**Regras:**
- `requer_aprovacao` é configurado por proposta (workflow opcional)
- Somente EDITOR/OWNER pode enviar para aprovação
- Somente APROVADOR/OWNER pode aprovar ou rejeitar
- Rejeição retorna para `CPU_GERADA` (editável), não arquiva

### 3. Fila de Aprovação (GET /propostas/aprovacoes)

- Lista propostas `AGUARDANDO_APROVACAO` onde o user é APROVADOR ou OWNER
- No frontend: `ApprovalQueuePage` em `/propostas/aprovacoes`
- Empty state quando nenhuma proposta aguarda aprovação

### 4. Histórico de Versões

- `GET /propostas/root/{root_id}/versoes` — lista todas as versões de uma família
- No frontend: `ProposalHistoryPanel` como Accordion colapsável no `ProposalDetailPage`
- Mostra versão, código, status, data e flag atual/fechada

---

## Arquivos principais criados/modificados

### Backend
- `app/alembic/versions/022_proposta_versionamento.py` ← NOVO
- `app/backend/models/enums.py` ← AGUARDANDO_APROVACAO
- `app/backend/models/proposta.py` ← 9 campos + UniqueConstraint
- `app/backend/core/dependencies.py` ← ACL via root_id
- `app/backend/repositories/proposta_repository.py` ← 3 métodos novos
- `app/backend/services/proposta_versionamento_service.py` ← NOVO
- `app/backend/schemas/proposta.py` ← campos + request schemas
- `app/backend/api/v1/endpoints/propostas.py` ← 5 endpoints novos
- `app/backend/tests/unit/test_proposta_versionamento_service.py` ← NOVO (12 testes)
- `app/backend/tests/unit/test_proposta_versionamento_endpoints.py` ← NOVO (8 testes)

### Frontend
- `app/frontend/src/shared/services/api/proposalsApi.ts` ← tipos + 6 métodos
- `app/frontend/src/features/proposals/components/ProposalHistoryPanel.tsx` ← NOVO
- `app/frontend/src/features/proposals/pages/ApprovalQueuePage.tsx` ← NOVO
- `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx` ← botões condicionais + painel histórico
- `app/frontend/src/features/proposals/routes.tsx` ← rota aprovacoes
- `app/frontend/src/shared/utils/format.ts` ← label AGUARDANDO_APROVACAO
- `app/frontend/src/shared/components/StatusBadge.tsx` ← cor amber

---

## Métricas finais

| Métrica | Resultado |
|---|---|
| Testes pytest | **179 PASS, 0 FAIL** |
| TypeScript errors | **0** |
| Migration | **022 aplicada** |
| Backfill | **0 rows NULL** |
| Endpoints novos | **5** |
| Componentes frontend novos | **2** (ProposalHistoryPanel, ApprovalQueuePage) |
| Testes novos | **20** (12 service + 8 endpoint) |

---

## Handoff para QA

- Sprint marcada como **TESTED** no BACKLOG
- Milestone 6 (Proposta Completa) concluído: F2-01 + F2-02 + F2-03 + F2-04 + F2-05 + F2-06 + F2-07 + F2-08 + F2-09
- Próxima sprint: F2-10 (Milestone 7 — Compras e Negociação)
