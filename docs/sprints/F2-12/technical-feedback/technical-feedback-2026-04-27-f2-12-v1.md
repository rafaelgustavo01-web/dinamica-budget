# Technical Feedback - Sprint F2-12 (Refatoração Importação TCPO)

> Version: v1
> Date: 2026-04-27
> QA: Amazon Q
> Backlog status on entry: TESTED

## Executive Summary

Sprint F2-12 aceita. Débito técnico resolvido corretamente. A detecção de serviço pai foi refatorada de uma condição frágil (apenas `SER.CG`) para um AND triplo robusto (`startswith("SER.")` + `font.bold=True` + `alignment.indent==0`), eliminando o bug de orfanamento de insumos causado por subserviços classificados como `SER.CG`. 8 testes unitários cobrem todos os cenários do briefing incluindo variantes de prefixo. Nenhuma regressão introduzida.

## Acceptance Decision

- Decision: DONE
- Reason: Todos os critérios de aceite atendidos. Lógica de detecção correta e mais robusta que a versão anterior. Testes expandidos de 6 para 8 cobrindo variantes de prefixo SER. e classes não-SER. Nenhum outro import afetado.
- Next role owner: Research AI + Product Owner

## Confirmed Wins

- `app/backend/services/etl_service.py`: Condição `is_parent` agora usa AND triplo (`startswith("SER.")` + `bold` + `indent==0`). Generalização para `startswith("SER.")` cobre variantes `SER.CH`, `SER.MO` presentes no catálogo TCPO. Cross-check de alinhamento torna a detecção mais resiliente a edge cases.
- `app/backend/services/etl_service.py`: `is_subservice` derivado como negação de `is_parent` dentro do prefixo `SER.` — lógica limpa e mutuamente exclusiva.
- `app/backend/services/etl_service.py`: `parse_converter_datacenter` inalterado — usa `values_only=True`, não afetado pela mudança.
- `app/backend/tests/unit/test_etl_service.py`: 8 testes com mocks de células openpyxl. Fixture `clear_cache` com `autouse=True` garante isolamento do singleton. `_MockWorkbook` simula interface openpyxl sem dependência de arquivo real.
- Regressão: 197 PASS, 12 erros ambientais asyncpg/Windows não relacionados à sprint.

## Findings

### Info — Alta complexidade ciclomática em `parse_tcpo_pini` (CC=18)
- File: `app/backend/services/etl_service.py` linha 103
- Problem: Complexidade ciclomática 18 — pré-existente, levemente aumentada pelo cross-check de alinhamento.
- Observation: Esperado dado o volume de branches de parsing. Candidato para refatoração em sprint futura se necessário.

### Info — Alta complexidade ciclomática em `execute_load` (CC=25)
- File: `app/backend/services/etl_service.py` linha 276
- Problem: Pré-existente, não introduzido por F2-12.
- Observation: Candidato para extração de helpers em sprint de hardening.

### Low — `_make_row` retorna tupla de 6 células
- File: `app/backend/tests/unit/test_etl_service.py` linha 30
- Problem: Helper de teste retorna múltiplos valores — detectado pelo scanner como potencial fonte de erro.
- Observation: Funcional e sem impacto em produção. Aceitável em contexto de teste.

## Rework Instructions

Nenhum rework necessário. Sprint aceita como DONE.

## Scorecard

| Criterion | Result |
|-----------|--------|
| Plan scope delivered | YES |
| Tests acceptable | YES (8 PASS — 6 originais + 2 novos do ajuste) |
| Lint acceptable | YES |
| Documentation complete | YES (walkthrough atualizado; technical-review ausente — não bloqueador) |
| Backlog state correct | YES (atualizado para DONE) |

## Closeout Updates

- Walkthrough movido de `docs/sprints/F2-12/walkthrough/done/` para `docs/sprints/F2-12/walkthrough/reviewed/`.
- Sprint F2-12 atualizada para `DONE` no BACKLOG.
- Inbox disparado para Research AI (MINE_ROADMAP) e Product Owner (INTAKE_NEXT).
