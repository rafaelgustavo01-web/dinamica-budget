# Walkthrough — S-04 Endurecer Segurança e RBAC (Consolidado)

## Status
`TESTED`

## O que mudou (Consolidado Kimi & Gemini)
- Reintroduzida a validação `require_cliente_access` em endpoints de leitura sensíveis:
  1. **GET `/busca/associacoes`**: Protegido.
  2. **GET `/servicos/{item_id}/versoes`**: Protegido.
  3. **GET `/servicos/`**: Protegido quando `cliente_id` é informado.
- Implementados testes de regressão específicos em `app/backend/tests/unit/test_security_s04.py`.
- Atualizados testes de governança e segurança legados para refletir as novas restrições.
- Execução completa do Checklist OWASP API (13/14 PASS).

## Critérios de Aceite
- Todos os endpoints de READ sensíveis validam acesso ao cliente: ✅
- Nenhum endpoint expõe dados cross-client sem autorização: ✅
- Testes de regressão cobrem autorização: ✅ (85 testes PASS)
- Checklist OWASP consolidado e documentado: ✅

## Verificação Técnica
- Execução de `pytest app/backend/tests/unit/ -v`: 85/85 PASS.
- Validação manual de tokens, expiração e rate limiting conforme checklist.

## Notas para o QA (OpenCode)
A implementação foi realizada em conjunto pelos agentes Kimi e Gemini. O foco foi re-estabelecer o isolamento de dados por cliente em operações de leitura que não são puramente catalográficas (associações e histórico de versões).
