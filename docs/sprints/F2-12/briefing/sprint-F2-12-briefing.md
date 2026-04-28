# Sprint F2-12: Refatoração Importação TCPO (Débito Técnico)

## Objetivo
Refatorar a lógica de extração do arquivo Excel "Composições TCPO - PINI.xlsx" na aba "Composições analíticas" no serviço `etl_service.py` (método `parse_tcpo_pini`). O objetivo é resolver um bug arquitetural onde um serviço composto por outros subserviços quebrava a hierarquia devido à classificação unânime de `SER.CG`.

## Contexto Técnico e Descoberta
O sistema atual usa unicamente a string `"SER.CG"` na coluna `CLASS` para identificar o Serviço Pai, assumindo que qualquer linha seguinte que não seja `"SER.CG"` é um insumo. No entanto, subserviços dentro da composição também são classificados como `"SER.CG"`, o que faz o sistema considerá-los erroneamente como um novo Serviço Pai, orfanando os insumos.

Após análise da estrutura original do Excel (`openpyxl`), foi descoberto que a PINI utiliza a formatação em **Negrito (`font.bold = True`)** exclusivamente na célula de Descrição do Serviço Pai da composição. Os subserviços, mesmo sendo `SER.CG`, não possuem negrito. Como mecanismo de *cross-check*, os itens Pai também estão alinhados à esquerda, enquanto insumos e subserviços podem apresentar indentação (embora a flag de negrito seja determinística).

## Critérios de Aceite
1. `app/backend/services/etl_service.py` modificado para usar a detecção de `font.bold` da célula de descrição para definir `current_parent_codigo`.
2. A lógica deve tratar linhas `"SER.CG"` sem negrito como subserviços vinculados ao `current_parent_codigo` vigente (adicionando-as à lista de relações sem sobrescrever o ponteiro do Pai).
3. O fallback de alinhamento (`alignment.indent` ou fallback visual) pode ser utilizado se necessário para complementar o cross-check do negrito.
4. Os testes unitários do ETL (`backend/tests/unit/test_etl_service.py` ou equivalentes) devem cobrir essa nova árvore lógica de "Serviço composto por Subserviço".
5. Nenhum outro import (`Converter em Data Center` ou `BCU`) deve ser afetado.

## Artefatos e Paths
- **Código alvo:** `app/backend/services/etl_service.py`
- **Briefing:** `docs/sprints/F2-12/briefing/sprint-F2-12-briefing.md`
- **Plan:** `docs/sprints/F2-12/plans/2026-04-27-refatoracao-tcpo.md`

## Worker Delegado
Kimi (kimi-k2.6)