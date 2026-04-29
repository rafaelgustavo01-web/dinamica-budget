# Walkthrough — F3-02 Correções críticas de UI/UX

Data: 2026-04-29  
Status: TESTED

## Checklist funcional

- [x] CPU não corta colunas principais em telas menores; tabela ganha scroll horizontal.
- [x] Match Review não corta ações/colunas em notebook; tabela ganha scroll horizontal.
- [x] Nova Proposta sem cliente selecionado mostra orientação clara e não tenta criar registro inválido.
- [x] Importar PQ diferencia erro de carregamento de proposta de estado normal/loading.
- [x] CPU diferencia erro de carregamento de itens/proposta de lista vazia.
- [x] Admin/aprovador consegue descobrir a Fila de Aprovação pela navegação.
- [x] Histograma não restringe divergências apenas a equipamento/EPI/ferramenta.

## Evidência de gates

Executado em `app/frontend`:

```text
npm ci --cache /tmp/npm-cache --prefer-offline
npm run build
npm run test
```

Resultado: build OK e testes OK — 13 PASS.

## Pendências não bloqueantes

- Warning existente em teste de `ExpandableTreeRow`: HTML inválido por `tr` aninhado em `div` dentro de `Collapse`.
- Warning de bundle/chunk grande no Vite.
