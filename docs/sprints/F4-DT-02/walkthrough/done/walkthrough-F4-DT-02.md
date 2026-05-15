# Walkthrough — F4-DT-02

## O que mudou
- Redução de falso negativo no status de match após restart/múltiplos workers.
- Correção visual de encoding em itens expandidos.
- Contratos de payload mais rígidos com Pydantic.

## Validação
- git diff --check: PASS.
- grep U+FFFD em app/frontend/src: PASS, sem ocorrências.
- backend compileall: PASS.
- backend pytest focado: 94 passed, 8 warnings.
- frontend npm audit: 0 vulnerabilities.
- frontend npm run lint: PASS.
- frontend npm test -- --run: 13 tests PASS.
- frontend npm run build: PASS, com warning conhecido de chunk > 500 kB.
