# F3-05 — Hotfix PQ Match + TCPO Recursive Tree

## Objetivo
Corrigir dois bugs reportados em testes de uso sem quebrar fluxos existentes:
1. Após importar PQ, habilitar corretamente o passo **2. Match Inteligente**.
2. Explodir serviços TCPO de forma recursiva quando um serviço contém outro serviço na composição.

## Premissas obrigatórias
- Mudança incremental e reversível.
- Não alterar produção.
- Não recriar arquitetura de importação nesta sprint.
- Não misturar hardening amplo ou Smart Import adaptativo neste hotfix.
- Preservar contratos existentes quando possível; qualquer ajuste de contrato deve ter fallback.

## Divisão por agente
- **Codex / backend:** status pós-importação PQ; parser TCPO por hierarquia/indentação; testes unitários.
- **Claude / frontend:** habilitação do botão/fluxo de Match; árvore recursiva lazy-load; labels menos técnicos.
- **Kimi / hardening:** revisar riscos de ciclo, transação, N+1 e race condition; não aplicar refactors grandes nesta sprint.
- **Gemini / QA:** validar critérios e regressão após integração.

## Escopo
### Backend
- Garantir que importação com itens válidos deixa proposta em estado apto ao match.
- Corrigir carga TCPO para preservar relação pai → subserviço → filhos, em vez de achatar tudo no pai raiz.
- Cobrir exemplo `3R0412140000002230 -> 3R0412140000002233 -> filhos`.

### Frontend
- Habilitar Match com base em existência de itens PQ e/ou status consistente do backend.
- Permitir expansão recursiva no Catálogo de Serviços para filhos `SERVICO`.
- Remover/amenizar labels técnicos em árvore quando possível.

## Critérios de aceite
- Upload PQ com itens válidos habilita Match sem reload manual.
- Proposta com PQ já importada habilita Match ao reabrir tela.
- Serviço TCPO com subserviço expande pelo menos 3 níveis sem erro.
- Build frontend passa.
- Testes backend focados passam.
- `git diff --check` passa.

## Riscos
- Dados TCPO já carregados podem exigir recarga para materializar hierarquia corrigida.
- Recursão precisa manter proteção contra ciclo/profundidade.
