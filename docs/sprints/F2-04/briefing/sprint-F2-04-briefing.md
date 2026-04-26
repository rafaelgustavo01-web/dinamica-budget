# Sprint F2-04 — Briefing

**Sprint:** F2-04
**Titulo:** CPU Detalhada — Breakdown de Insumos e BDI Dinamico
**Worker:** kimi-k2.5 (Kimi CLI)
**Status:** TODO
**Data:** 2026-04-25

---

## Objetivo

Expor o breakdown completo de insumos por item da CPU (material, MO, equipamento) via API e permitir que o BDI seja recalculado dinamicamente sem regerar toda a CPU. Desbloquear a pagina de CPU no frontend com dados reais e accordion de insumos.

## Criterios de Aceite

- GET /propostas/{id}/cpu/itens/{item_id}/composicoes retorna lista de insumos com custos
- POST /propostas/{id}/cpu/recalcular-bdi atualiza BDI e totais sem re-explodir composicoes
- ProposalCpuPage desbloqueiada: mostra itens reais, botao "Gerar CPU" e "Recalcular BDI"
- CpuTable com accordion expandindo insumos por item (Material/MO/Equipamento)
- Totais direto/indireto/geral visiveis no header da pagina
- npx tsc --noEmit sem erros
- python -m pytest backend/tests/ com 115+ PASS, 0 FAIL

## Plano

Arquivo: `docs/sprints/F2-04/plans/2026-04-25-cpu-detalhada.md`

7 tasks:
1. Schemas ComposicaoDetalheResponse + RecalcularBdiRequest/Response
2. Repository: list_by_proposta_item em PropostaItemComposicaoRepository
3. Service: recalcular_bdi + listar_composicoes_item em CpuGeracaoService
4. Endpoints: GET /cpu/itens/{id}/composicoes + POST /cpu/recalcular-bdi
5. Frontend API: tipos + listCpuItens/getComposicoes/recalcularBdi/gerarCpu
6. CpuTable reescrita com accordion de insumos
7. ProposalCpuPage desbloqueada com BDI dinamico

## Contexto tecnico

- Backend CPU service: `app/backend/services/cpu_geracao_service.py`
- CPU endpoint existente: `app/backend/api/v1/endpoints/cpu_geracao.py` — prefixo `/propostas/{id}/cpu`
- PropostaItem ja tem: custo_material_unitario, custo_mao_obra_unitario, custo_equipamento_unitario, custo_direto_unitario, percentual_indireto
- PropostaItemComposicao model: `app/backend/models/proposta.py` — tem custo_unitario_insumo, custo_total_insumo, tipo_recurso, nivel, e_composicao
- PropostaItemRepository: `app/backend/repositories/proposta_item_repository.py`
- PropostaItemComposicaoRepository: `app/backend/repositories/proposta_item_composicao_repository.py`
- Frontend CPU page atual: `app/frontend/src/features/proposals/pages/ProposalCpuPage.tsx` — bloqueada com ContractNotice, BDI hard-coded em estado local
- CpuTable atual: `app/frontend/src/features/proposals/components/CpuTable.tsx` — usa CpuItem simples

## Dependencias

- F2-03 pode rodar em paralelo (nao ha conflito de arquivos)
- S-11 DONE (CpuGeracaoService, PropostaItemComposicao, explosao de composicoes)
