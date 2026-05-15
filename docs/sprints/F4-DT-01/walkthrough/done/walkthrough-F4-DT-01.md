# Walkthrough — F4-DT-01 QA Hygiene + Backlog/Registry Cleanup

**Data:** 2026-05-15  
**Worker:** kimi-k2.5  
**Sprint:** F4-DT-01

---

## Resumo

Sprint de higiene técnica e limpeza de registros executada com sucesso. Quatro itens de escopo fechado foram tratados sem regressões.

---

## Itens Executados

### 1. MSW handler faltante
- **Arquivo:** `app/frontend/src/features/proposals/pages/__tests__/ProposalDetailPage.test.tsx`
- **Mudança:** Adicionado mock `GET /api/v1/propostas/p1/items` retornando `[]` no `setupCommonHandlers()`.
- **Evidência:** `npm test` executou 4 testes de `ProposalDetailPage` sem mensagens de erro no stderr.

### 2. Warning de nesting HTML em ExpandableTreeRow
- **Arquivo:** `app/frontend/src/features/compositions/components/ExpandableTreeRow.tsx`
- **Mudança:** Filhos recursivos do `Collapse` envolvidos em `<table><tbody>`.
- **Evidência:** `npm test` executou 3 testes de `ExpandableTreeRow` sem warning de hydration.

### 3. Vulnerabilidade xlsx
- **Arquivos:** `app/frontend/package.json`, `app/frontend/src/features/bcu/BcuUploadPage.tsx`
- **Mudança:** `xlsx@0.18.5` → `@e965/xlsx@0.20.3`.
- **Evidência:** `npm audit` reportou **0 vulnerabilities** (anteriormente 1 HIGH).

### 4. Normalização de workers.json
- **Arquivo:** `templates/workers.json`
- **Mudança:** kimi-k2.5 liberado, timestamps atualizados, notas refletindo conclusão da sprint.

---

## Gates

```
git diff --check        ✅
npm run lint            ✅
npm test                ✅ 13 PASS
npm run build           ✅
npm audit               ✅ 0 vulnerabilities
```

---

## Backlog

- `F4-DT-01` atualizado de **TODO** → **TESTED** em `docs/shared/governance/BACKLOG.md`.

---

## Próximos Passos (fora do escopo desta sprint)

- Aguardar QA formal para promoção de F4-DT-01 para DONE.
- Retomar M7/Compras quando priorizado pelo PO.
