# Technical Review — Sprint F2-04

> **Data:** 2026-04-25
> **Sprint:** F2-04 — CPU Detalhada + BDI Dinâmico
> **Worker:** kimi-k2.5
> **Status:** TESTED

---

## Resumo das Mudanças

### 1. Schemas
- **Arquivo:** `app/backend/schemas/proposta.py`
- `ComposicaoDetalheResponse`: breakdown de insumos com custos, tipo_recurso, nivel.
- `RecalcularBdiRequest`: percentual_bdi com validação `ge=0, le=100`.
- `RecalcularBdiResponse`: totais e contagem de itens recalculados.

### 2. Repository
- **Arquivo:** `app/backend/repositories/proposta_item_composicao_repository.py`
- `list_by_proposta_item` ordenado por `nivel.asc()` para exibir árvore hierárquica.

### 3. Service
- **Arquivo:** `app/backend/services/cpu_geracao_service.py`
- `recalcular_bdi(proposta_id, percentual_bdi)`: recalcula preços sem re-explodir composições.
- `listar_composicoes_item(proposta_item_id)`: retorna insumos de um item.

### 4. Endpoints
- **Arquivo:** `app/backend/api/v1/endpoints/cpu_geracao.py`
- `GET /propostas/{id}/cpu/itens/{item_id}/composicoes` — 200 com lista de insumos.
- `POST /propostas/{id}/cpu/recalcular-bdi` — 200 com totais atualizados.

### 5. Frontend API
- **Arquivo:** `app/frontend/src/shared/services/api/proposalsApi.ts`
- Tipos `ComposicaoDetalhe`, `CpuItemDetalhado`, `RecalcularBdiRequest/Response`.
- Métodos: `listCpuItens`, `getComposicoes`, `recalcularBdi`, `gerarCpu`.

### 6. CpuTable
- **Arquivo:** `app/frontend/src/features/proposals/components/CpuTable.tsx`
- Reescrita com accordion expandindo insumos por item.
- Colunas separadas: Material, MO, Equipamento, Direto Unit., BDI, Total.
- Chips de tipo de recurso (MO/EQUIPAMENTO/MAT) nos insumos.

### 7. ProposalCpuPage
- **Arquivo:** `app/frontend/src/features/proposals/pages/ProposalCpuPage.tsx`
- Desbloqueada: dados reais via TanStack Query.
- Botão "Gerar CPU" (primeira geração) / "Recalcular BDI" (atualização dinâmica).
- Totais direto/indireto/geral no header.
- Feedback de sucesso/erro via Alert.

## Regressão
- Backend: **115 passed, 0 failed** (11 errors em integration tests por DB indisponível — preexistente).
- Frontend: `npx tsc --noEmit` — 0 erros.

## Riscos
- **Baixo:** `percentual_indireto` reutilizado como coluna de BDI; sem migration necessária.
- **Baixo:** Frontend consome API existente; sem breaking changes.
- **Médio:** `ComposicaoDetalheResponse.tipo_recurso` serializado como string; depende do enum SQLAlchemy ter `.value`.

## Checklist
- [x] Breakdown de insumos por item
- [x] BDI dinâmico por proposta
- [x] Gerar CPU funcional
- [x] Totais visíveis
- [x] Material/MO/Equipamento separados
- [x] 115+ testes PASS
- [x] TypeScript 0 erros
