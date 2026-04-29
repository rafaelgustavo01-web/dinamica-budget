# Technical Review — F3-02 Demo Readiness UI/UX Fixes

Data: 2026-04-29  
Status: TESTED  
Worker: gedAI + Claude Code assistido

## Escopo executado

Correções críticas de UI/UX priorizadas a partir da auditoria F3-01 para reduzir risco na apresentação desta semana.

## Alterações

- CPU: `CpuTable` passou a usar `TableContainer` com scroll horizontal e largura mínima para evitar corte de colunas/ações em notebook.
- Match Review: tabela principal agora tem container com overflow horizontal e largura mínima.
- Criar Proposta: adicionado guard/empty state quando não há cliente selecionado.
- Importar PQ: erro ao carregar proposta agora exibe `Alert` explícito e bloqueia fluxo indevido.
- CPU Page: erros de proposta/itens agora aparecem como erro real, não como estado vazio; ações ficam desabilitadas quando há erro de carregamento.
- Fila de Aprovação: adicionada entrada de navegação visível para admin/aprovador.
- Histograma: divergências passam a ser filtradas pela tabela atual diretamente, cobrindo também abas genéricas como encargos/mobilização quando o backend retornar divergências para essas tabelas.

## Gates

- `npm ci --cache /tmp/npm-cache --prefer-offline`: PASS.
- `npm run build`: PASS.
- `npm run test`: PASS — 4 arquivos, 13 testes.

## Observações

- O teste existente de `ExpandableTreeRow` mantém warning de DOM inválido (`tr` dentro de `div`) já observado fora do escopo desta sprint. Não falha o gate, mas deve entrar no backlog de polimento técnico se houver tempo.
- Build mantém warning de chunk > 500 kB, também não bloqueante para a apresentação.
