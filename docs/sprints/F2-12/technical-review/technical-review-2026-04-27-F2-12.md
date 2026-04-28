# Technical Review - Sprint F2-12: Refatoracao Importacao TCPO

**Data:** 2026-04-27
**Worker:** kimi-k2.6
**Branch:** main

## Arquivos alterados

| Arquivo | Tipo | Descricao |
|---|---|---|
| `app/backend/services/etl_service.py` | Modificado | `parse_tcpo_pini`: iterador `values_only=False`, deteccao `font.bold`, roteamento subservico |
| `app/backend/tests/unit/test_etl_service.py` | Novo | 6 testes unitarios com mocks openpyxl |

## Checklist de qualidade

- [x] Codigo segue padrao do repositorio (PEP 8, type hints)
- [x] Nenhum import removido ou alterado indevidamente
- [x] `parse_converter_datacenter` inalterado
- [x] Testes cobrem caso feliz + edge cases (orfao, multiplos pais, mixed children, variacoes de prefixo SER.)
- [x] Cache do singleton limpo entre testes (fixture `clear_cache`)
- [x] Regressao: 8 passed no modulo ETL, 197 passed geral, 0 novos failures

## Decisoes tecnicas

1. **Por que `values_only=False` em vez de `values_only=True`?**
   - `values_only=True` descarta informacoes de estilo. `font.bold` e `alignment.indent` sao necessarios para distinguir pai de subservico.
   - Custo de memoria aceitavel: arquivo TCPO tipico tem ~40-60k linhas.

2. **Por que `startswith("SER.")` em vez de `== "SER.CG"`?**
   - A PINI usa varias classificacoes de servico: `SER.CG`, `SER.MO`, `SER.CH`, etc.
   - `startswith("SER.")` captura todas as variacoes sem manutencao manual de enum.
   - Classes que nao comecam com `SER.` sao sempre insumos diretos, independente do nome.

3. **Cross-check `alignment.indent == 0`**
   - Servico pai requer TRES condicoes simultaneas: `classe.startswith("SER.")` AND `is_bold` AND `alignment.indent == 0`.
   - Isso evita falsos positivos se uma celula accidentalmente estiver em negrito.

4. **Por que `_MockWorkbook` em vez de `MagicMock` puro?**
   - `MagicMock.__getitem__` intercepta chamadas de forma peculiar no Python. Um objeto simples com `__getitem__` eh mais previsivel e evita o erro `takes 1 positional argument but 2 were given`.

## Observacoes para QA

- Nenhum efeito colateral esperado em outros modulos. O ETL service soh eh usado pelo endpoint `/admin/etl/upload-tcpo`.
- O singleton `etl_service` compartilha cache entre chamadas, mas os testes limpam o cache.
- Performance: leitura com `values_only=False` eh ligeiramente mais lenta, mas imperceptivel para o tamanho da TCPO.

## Riscos

| Risco | Severidade | Mitigacao |
|---|---|---|
| PINI muda convencao de negrito | Baixa | Parser centralizado em um unico metodo; ajuste eh local |
| Memory pressure em arquivos muito grandes | Baixa | Arquivo tipico < 10MB; iterador eh lazy |
