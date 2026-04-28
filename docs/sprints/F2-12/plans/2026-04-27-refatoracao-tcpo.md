# Plano de Implementação: Refatoração Importação TCPO (Sprint F2-12)

**Data:** 2026-04-27
**Autor:** PO / Scrum Master / Supervisor AI (Gemini)

## 1. Visão Geral
Modificar a função `parse_tcpo_pini` no `etl_service.py` para suportar corretamente subserviços, evitando a quebra de vínculo hierárquico na composição analítica. 

## 2. A Solução
Substituir a lógica atual que usa somente `CLASS == "SER.CG"` por uma lógica combinada de prefixo `CLASS.startswith("SER.")` E formatação visual (`font.bold` e `alignment.indent`):

### Fluxo de Parse Sugerido:
1. Ler o arquivo `.xlsx` normalmente usando `openpyxl` sem `values_only=True` na iteração da TCPO.
2. Ao iterar as linhas, extrair a célula de descrição (ex: `desc_cell = row[1]`) e de código (ex: `codigo_cell = row[0]`).
3. Avaliar `is_bold = desc_cell.font.bold if desc_cell.font else False`.
4. Avaliar `indent = codigo_cell.alignment.indent if codigo_cell.alignment else 0`.
5. Condicional de Roteamento:
   - **Se `classe_clean.startswith("SER.")` E `is_bold` E `indent == 0`:** Inicia nova composição. Define `current_parent_codigo = codigo`. Adiciona aos `itens` como `"SERVICO"`.
   - **Se `classe_clean.startswith("SER.")` E (não é bold OU indent > 0):** Trata-se de um subserviço consumido pelo serviço atual. Adiciona aos `itens` como `"SERVICO"` (se ainda não visto), mas NÃO altera o `current_parent_codigo`. Adiciona à lista de `relacoes` do pai atual.
   - **Outras classes (não começam com SER.):** Adiciona aos `itens` (tipo do recurso correspondente) e adiciona à lista de `relacoes` do pai atual.

## 3. Considerações Técnicas
- **Desempenho (openpyxl):** Atualmente o código usa `.iter_rows(values_only=True)`. Com `values_only=True`, as informações de fonte/estilo são perdidas. Será necessário mudar para `.iter_rows(values_only=False)` para acessar `.font.bold`, e então usar `.value` de cada célula, ou usar `values_only=False` especificamente para extrair a formatação. Isso tem um leve custo de memória, mas aceitável para o tamanho da TCPO (normalmente ~40-60 mil linhas).
- **Fallback:** Como cross-check sugerido, itens pai também não possuem `alignment.indent` (alinhado a 0).
- **Testes:** Os mocks de teste que emulam planilhas TCPO no pytest precisam ser atualizados para prover o mock das propriedades `.font.bold` dos objetos cell simulados.

## 4. Ordem de Tarefas (Para o Worker)
1. Modificar `app/backend/services/etl_service.py` (remover `values_only=True` da linha iteradora específica do TCPO, para permitir leitura de estilos).
2. Implementar lógica `font.bold` e tratar o caso do subserviço.
3. Atualizar/Adicionar testes unitários pertinentes.
4. Validar tipagem (`tsc` no front não será afetado, mas rodar `pytest`).
5. Gerar o `walkthrough` de entrega e abrir handoff para QA.