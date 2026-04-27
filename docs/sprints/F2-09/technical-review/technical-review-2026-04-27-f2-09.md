# Technical Review — Sprint F2-09

**Sprint:** F2-09 — Versionamento de Propostas + Workflow de Aprovação
**Worker:** claude-sonnet-4-6
**Data:** 2026-04-27
**Status:** TESTED ✅

---

## Resultado dos Critérios de Aceite

| Critério | Resultado |
|---|---|
| Migration 022 aplicada sem erro (autocommit_block correto) | ✅ OK |
| `SELECT count(*) FROM propostas WHERE proposta_root_id IS NULL` = 0 | ✅ 0 rows |
| **179 PASS, 0 FAIL** no pytest | ✅ 179 passed |
| **0 erros** no `tsc --noEmit` | ✅ 0 errors |
| `nova_versao` retorna 201 com `numero_versao` incrementado | ✅ |
| Versão anterior com `is_versao_atual=FALSE`, `is_fechada=TRUE` | ✅ |
| Workflow de aprovação funcional (enviar → aprovar/rejeitar) | ✅ |
| `GET /aprovacoes` filtra por papel do usuário | ✅ |
| `ProposalHistoryPanel` renderiza lista de versões | ✅ |
| `ApprovalQueuePage` com ações aprovar/rejeitar + empty state | ✅ |
| Botões condicionais corretos no `ProposalDetailPage` | ✅ |
| Badge AGUARDANDO_APROVACAO com cor amber (pendente) | ✅ |

---

## O que foi entregue

### Backend

#### Migration 022 (`app/alembic/versions/022_proposta_versionamento.py`)
- `AGUARDANDO_APROVACAO` adicionado ao enum `status_proposta_enum` via `autocommit_block` (PostgreSQL não suporta ADD VALUE dentro de transação)
- 9 colunas adicionadas à `operacional.propostas`: `proposta_root_id`, `numero_versao`, `versao_anterior_id`, `is_versao_atual`, `is_fechada`, `requer_aprovacao`, `aprovado_por_id`, `aprovado_em`, `motivo_revisao`
- Backfill: `proposta_root_id = id`, `numero_versao = 1`, `is_versao_atual = TRUE` para todas as propostas existentes
- FK self-referencial `versao_anterior_id → propostas.id` (nullable)
- FK `aprovado_por_id → usuarios.id` (nullable)
- UniqueConstraint `(proposta_root_id, numero_versao)` — garante unicidade de versões por root

#### Model (`app/backend/models/proposta.py`)
- 9 campos adicionados a `Proposta`
- `__table_args__` convertido de dict para tuple para suportar `UniqueConstraint`
- `foreign_keys="[Proposta.criado_por_id]"` adicionado ao relacionamento `criado_por` para resolver ambiguidade com `aprovado_por_id` (SQLAlchemy `AmbiguousForeignKeysError`)

#### Dependencies (`app/backend/core/dependencies.py`)
- `require_proposta_role`: agora lê `proposta.proposta_root_id` e usa esse valor para resolver a ACL via `PropostaAclService`
- Retrocompatível: propostas existentes têm `proposta_root_id = id` após backfill

#### Repository (`app/backend/repositories/proposta_repository.py`)
- `max_numero_versao(root_id)` — retorna o maior `numero_versao` para uma família de versões
- `list_by_root(root_id)` — lista todas as versões ordenadas por `numero_versao`
- `list_aguardando_aprovacao()` — retorna todas as propostas com `status = AGUARDANDO_APROVACAO`

#### Service (`app/backend/services/proposta_versionamento_service.py`)
- `nova_versao`: clona metadados da versão atual, fecha-a, cria nova com `numero_versao + 1`. Código gerado: `{base}-v{N}` (garante "ORC-001-v2" → "ORC-001-v3", não "ORC-001-v2-v3")
- `enviar_aprovacao`: `CPU_GERADA → AGUARDANDO_APROVACAO` (só se `requer_aprovacao=True`)
- `aprovar`: `AGUARDANDO_APROVACAO → APROVADA` com `aprovado_por_id` e `aprovado_em`
- `rejeitar`: `AGUARDANDO_APROVACAO → CPU_GERADA` com `motivo_revisao` opcional

#### Schemas (`app/backend/schemas/proposta.py`)
- `PropostaResponse`: 9 campos novos todos `Optional`/`default=None` — retrocompatível com 158 testes F2-01..F2-08
- `PropostaNovaVersaoRequest`, `PropostaAprovarRequest`, `PropostaRejeitarRequest`

#### Endpoints (`app/backend/api/v1/endpoints/propostas.py`)
5 novos endpoints, todos declarados na ordem correta para evitar conflito com `/{proposta_id}`:
- `GET /propostas/aprovacoes` — fila de aprovação filtrada por papel APROVADOR/OWNER
- `GET /propostas/root/{root_id}/versoes` — lista versões de uma família
- `POST /propostas/{id}/nova-versao` — cria nova versão (requer EDITOR+)
- `POST /propostas/{id}/enviar-aprovacao` — submete para aprovação (requer EDITOR+)
- `POST /propostas/{id}/aprovar` — aprova proposta (requer APROVADOR+)
- `POST /propostas/{id}/rejeitar` — rejeita com motivo (requer APROVADOR+)

#### Testes
- `test_proposta_versionamento_service.py`: 12 testes cobrindo todos os fluxos do service
- `test_proposta_versionamento_endpoints.py`: 8 testes cobrindo os endpoints

### Frontend

#### `proposalsApi.ts`
- `StatusProposta` atualizado com `AGUARDANDO_APROVACAO`
- `PropostaResponse` atualizado com 9 campos de versioning/aprovação
- Métodos adicionados: `novaVersao`, `listarVersoes`, `enviarAprovacao`, `aprovar`, `rejeitar`, `filaAprovacoes`

#### `StatusBadge.tsx` + `format.ts`
- `AGUARDANDO_APROVACAO` mapeado para cor `pendente` (amber) no badge
- Label: "Aguardando aprovação"

#### `ProposalHistoryPanel.tsx` (novo)
- Tabela colapsável com todas as versões da proposta
- Colunas: número, código, status, data de criação, flag atual/fechada
- Navegação por clique na linha

#### `ApprovalQueuePage.tsx` (novo)
- Rota `/propostas/aprovacoes`
- Lista de propostas `AGUARDANDO_APROVACAO` onde user é APROVADOR/OWNER
- Botões inline: Aprovar (verde) e Rejeitar (vermelho)
- Dialog de rejeição com campo de motivo
- Empty state adequado: ícone + mensagem quando fila vazia

#### `ProposalDetailPage.tsx` (atualizado)
- Botões condicionais:
  - "Nova Versão" (EDITOR+, só em versão atual não fechada)
  - "Enviar para Aprovação" (EDITOR+, quando `requer_aprovacao=True` e `status=CPU_GERADA`)
  - "Aprovar" / "Rejeitar" (APROVADOR+, quando `status=AGUARDANDO_APROVACAO`)
- Seção "Histórico de Versões" colapsável com `ProposalHistoryPanel`
- Campo "Versão" exibido nos dados da proposta

#### `routes.tsx` (atualizado)
- Rota `aprovacoes` declarada ANTES de `:id` (React Router avalia em ordem)

---

## Decisões técnicas

| Decisão | Motivo |
|---|---|
| `autocommit_block` para ALTER TYPE | PostgreSQL não suporta ADD VALUE em transação |
| `foreign_keys` no relacionamento `criado_por` | Duas FKs para `usuarios` causam `AmbiguousForeignKeysError` sem especificar |
| ACL via `proposta_root_id` | Versões herdam permissões da raiz; sem duplicar entradas de ACL |
| `/aprovacoes` antes de `/{id}` | FastAPI e React Router avaliam rotas na ordem de declaração |
| `Optional` em todos os campos novos do schema | Retrocompatibilidade com 158 testes de F2-01..F2-08 |

---

## Regressão F2-08

- 158 testes originais: todos passando ✅
- 21 testes novos de F2-09 (12 service + 8 endpoint + 1 repository): todos passando ✅
- **Total: 179 PASS, 0 FAIL**

---

## Bugs encontrados e corrigidos durante a sprint

1. **`AmbiguousForeignKeysError`**: SQLAlchemy não conseguia inferir o join entre `Proposta` e `Usuario` com duas FKs. Corrigido adicionando `foreign_keys="[Proposta.criado_por_id]"` ao relacionamento `criado_por`.

2. **Enum schema errado na migration**: `operacional.status_proposta_enum` não existe — enum fica no schema `public`. Corrigido para `ALTER TYPE status_proposta_enum`.

3. **`NotFoundError` signature**: `NotFoundError` requer `(resource, identifier)`, não string única. Corrigido em todos os usos do service.

4. **Servidor de preview**: `.claude/launch.json` apontava para `frontend/` em vez de `app/frontend/`. Corrigido.

5. **TS error em `ConfirmationDialog`**: `confirmColor` não aceitava `"warning"`. Adicionado ao tipo union.
