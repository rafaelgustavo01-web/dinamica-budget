# Technical Review — F4-05 Smart Import Hardening

## Data
2026-05-15

## Escopo
- Smart Import authorization (Task 1)
- JSONB staging persistence (Task 2)
- Idempotent commit (Task 3)
- Brazilian decimal parser (Task 4)
- Normalize staging status/warnings (Task 5)
- Bound extraction + header validation (Task 6)
- Profile learner hardening (Task 7)

## Achados Tratados
| Risco | Status | Detalhe |
|-------|--------|---------|
| P0 — authorization gap em endpoints smart_import | FECHADO | `_authorize_job` com `require_proposta_role` / `require_cliente_access`; `for_update=True` no commit |
| P0 — commit duplicado/race condition | FECHADO | Guarda `committed_at` em `mapping_metadata`; row-level lock via `with_for_update()` |
| P0 — parsing decimal BR incorreto | FECHADO | `number_parser.py` com `parse_br_decimal` trata `1.234,56`, `1.234`, `1234.56` corretamente |
| P1 — mutação JSONB in-place | FECHADO | `_staging_rows` + `_replace_staging_rows` garante reatribuição do dict raiz |
| P1 — planilha sem limites de tamanho | FECHADO | `_MAX_ROWS = 5000`, `_MAX_COLUMNS = 80` no extractor; validação de aba existente |
| P1 — profile header row sem bounds | FECHADO | `HeaderDetector` rejeita `< 0` ou `>= len(rows)` |
| P1 — profile learner aceita campos arbitrários | FECHADO | `_ALLOWED_FIELDS` filtra `COLUMN_REMAP`; `_MAX_HEADER_ROW = 200` valida `HEADER_ROW_FIX` |

## Gates

### Testes focados smart_import
```
pytest tests/unit/smart_import -q
```
**Resultado: 77 passed, 8 warnings in 12.16s**

### Testes adjacentes de segurança
```
pytest tests/unit/test_security_p0.py tests/unit/test_security_s04.py tests/unit/test_proposta_acl_dependency.py -q
```
**Resultado: 28 passed, 1 failed, 1 warning**
- Falha: `test_list_servicos_validates_cliente_id_access_when_present` em `test_security_s04.py`
- Causa: Pydantic validation error `tipo_recurso=Query(None)` em `servicos.py` — **pré-existente, não relacionado a F4-05**

### Frontend build
```
cd app/frontend && npm run build
```
**Resultado: Falha em módulos `xlsx` e `@tanstack/react-virtual` — pré-existente, não relacionado a F4-05**
- Arquivos F4-05 no frontend: `smartImportApi.ts` e `SmartImportStagingPage.tsx` não geram erros TypeScript próprios

## Risco Residual
- Nenhum risco novo introduzido.
- Falha de build do frontend é de ambiente (dependências faltantes), não de código.
- Falha em `test_security_s04.py` é de regressão pré-existente em endpoint `servicos`, fora do escopo F4-05.

## Pendências
- Rodar `npm run build` após instalar `xlsx` e `@tanstack/react-virtual` no frontend (fora de escopo F4-05).
- QA deve validar commit idempotente em ambiente com banco real (teste unitário cobre lógica, mas não concorrência real).

## Decisão
Aprovado para merge local. Não dar push até QA validar.
