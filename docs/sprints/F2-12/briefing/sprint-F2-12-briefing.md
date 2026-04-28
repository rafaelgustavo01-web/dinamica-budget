# Sprint F2-12: Refatoração Importação TCPO (Débito Técnico)

## Objetivo
Refatorar a lógica de extração do arquivo Excel "Composições TCPO - PINI.xlsx" na aba "Composições analíticas" no serviço `etl_service.py` (método `parse_tcpo_pini`). O objetivo é resolver um bug arquitetural onde um serviço composto por outros subserviços quebrava a hierarquia devido à classificação unânime de `SER.CG`.

## Contexto Técnico e Descoberta
O sistema atual usa unicamente a string `"SER.CG"` na coluna `CLASS` para identificar o Serviço Pai, assumindo que qualquer linha seguinte que não seja `"SER.CG"` é um insumo. No entanto, subserviços dentro da composição também são classificados como `"SER.CG"` (ou outras variações como `"SER.MO"`, `"SER.CH"`), o que faz o sistema considerá-los erroneamente como um novo Serviço Pai, orfanando os insumos.

Após análise da estrutura original do Excel (`openpyxl`), foi descoberto que a PINI utiliza a formatação em **Negrito (`font.bold = True`)** na célula de Descrição do Serviço Pai e **Alinhamento à Esquerda (`alignment.indent = 0`)** na célula de Código. Os subserviços, mesmo começando com `SER.`, não possuem negrito e podem possuir indentação no Código. Como mecanismo de *cross-check*, os itens Pai devem ser validados por essas duas propriedades cruzadas.

## Critérios de Aceite
1. `app/backend/services/etl_service.py` modificado para usar a detecção de `font.bold` da célula de descrição e `alignment.indent == 0` da célula de código para definir `current_parent_codigo`.
2. A lógica deve identificar Serviços e Sub-serviços verificando se a classe começa com `"SER."` (`classe.startswith("SER.")`).
3. A lógica deve tratar linhas que começam com `"SER."` MAS que não são negrito (ou possuem indentação) como subserviços vinculados ao `current_parent_codigo` vigente (adicionando-as à lista de relações sem sobrescrever o ponteiro do Pai).
4. Classes que não começam com `"SER."` são tratadas como insumos normais.
5. Os testes unitários do ETL (`backend/tests/unit/test_etl_service.py` ou equivalentes) devem cobrir essa nova árvore lógica de "Serviço composto por Subserviço".
6. Nenhum outro import (`Converter em Data Center` ou `BCU`) deve ser afetado.

## Artefatos e Paths
- **Código alvo:** `app/backend/services/etl_service.py`
- **Briefing:** `docs/sprints/F2-12/briefing/sprint-F2-12-briefing.md`
- **Plan:** `docs/sprints/F2-12/plans/2026-04-27-refatoracao-tcpo.md`

## Worker Delegado
Kimi (kimi-k2.6)