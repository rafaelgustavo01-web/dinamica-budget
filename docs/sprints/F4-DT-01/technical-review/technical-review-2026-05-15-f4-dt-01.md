# Technical Review — F4-DT-01 QA Hygiene + Backlog/Registry Cleanup

**Data:** 2026-05-15  
**Worker:** kimi-k2.5  
**Sprint:** F4-DT-01  
**Status após review:** TESTED

---

## 1. Escopo Executado

| Item | Arquivo(s) | Ação | Motivo |
|---|---|---|---|
| MSW handler faltante | `app/frontend/src/features/proposals/pages/__tests__/ProposalDetailPage.test.tsx` | Adicionado `http.get('/api/v1/propostas/p1/items', () => HttpResponse.json([]))` em `setupCommonHandlers()` | `ProposalDetailPage` renderiza `ProposalItemsManager`, que dispara `GET /propostas/:id/items`. O setup MSW usava `onUnhandledRequest: 'error'`, gerando ruído nos logs de teste. |
| Nesting HTML inválido | `app/frontend/src/features/compositions/components/ExpandableTreeRow.tsx` | Componentes filhos recursivos envolvidos em `<table><tbody>` dentro do `Collapse` | `<tr>` renderizado diretamente dentro de `<div>` (Box) viola estrutura HTML de tabela e gera warning de hydration no console. A tabela intermediária preserva a semântica tabular. |
| Vulnerabilidade `xlsx` | `app/frontend/package.json`<br>`app/frontend/src/features/bcu/BcuUploadPage.tsx` | Substituído `xlsx@0.18.5` por `@e965/xlsx@0.20.3` (fork mantido da comunidade que corrige CVEs) | `npm audit` reportava HIGH: GHSA-4r6h-8v6p-xvw6 (Prototype Pollution) e GHSA-5pgg-2g8v-p4x9 (ReDoS). A versão 0.18.5 não possui correção upstream (`fixAvailable: false`). A troca é compatível de API (`XLSX.read`, `XLSX.utils.sheet_to_json`). |
| Registry cleanup | `templates/workers.json` | Normalizado: kimi-k2.5 liberado de `F4-DT-01`, `available: true`, `busy: false`, `reserved_for_sprint: null`; timestamps e notas atualizadas para PO/SM/Supervisor | Manter consistência do registry com estado real do pipeline após entrega. |

---

## 2. Gates Executados

| Gate | Comando | Resultado |
|---|---|---|
| git diff --check | `git diff --check` | ✅ Sem erros de whitespace |
| Frontend lint | `npm run lint` | ✅ Sem erros |
| Frontend test | `npm test` | ✅ 13 tests PASS, 0 stderr de MSW, 0 warning de nesting HTML |
| Frontend build | `npm run build` | ✅ tsc + vite build verdes |
| npm audit | `npm audit` | ✅ 0 vulnerabilities |

---

## 3. Decisão Técnica — xlsx

**Por que `@e965/xlsx` e não `exceljs` ou outra alternativa?**

- A superfície de uso no frontend é mínima (apenas `BcuUploadPage.tsx`, preview local de planilha).
- `exceljs` tem API diferente e bundle significativamente maior (~1 MB+), impactando chunk `BcuUploadPage`.
- `@e965/xlsx` mantém compatibilidade de API com `xlsx`, eliminando retrabalho e risco de regressão funcional.
- O fork é ativamente mantido e as vulnerabilidades reportadas (prototype pollution, ReDoS) estão corrigidas na 0.20.3.

**Plano de troca definitiva (se necessário no futuro):**
- Se o fork `@e965/xlsx` for descontinuado, avaliar migração para `exceljs` ou para parser server-side (backend já usa `openpyxl` e `pandas`).
- Monitorar `npm audit` em pipelines futuros.

---

## 4. Riscos

| Risco | Severidade | Mitigação |
|---|---|---|
| `@e965/xlsx` fork pode ficar desatualizado | Baixa | Uso restrito a preview local; backend já faz parsing seguro. Monitoramento via `npm audit`. |
| Tabela aninhada pode ter pequena diferença de estilo | Baixa | `<table style={{ width: '100%', borderCollapse: 'collapse' }}>` replica o contexto visual do pai. Smoke test validou renderização. |
| Mock `items` vazio simplifica teste | Baixa | O teste valida renderização do header e abas; comportamento de `ProposalItemsManager` é coberto por testes de integração/separados se necessário. |

---

## 5. Checklist

- [x] MSW handler faltante corrigido
- [x] Nesting HTML corrigido
- [x] Vulnerabilidade xlsx mitigada com substituição segura
- [x] workers.json normalizado
- [x] git diff --check verde
- [x] npm run lint verde
- [x] npm test verde (13/13)
- [x] npm run build verde
- [x] npm audit 0 vulnerabilities
- [x] BACKLOG.md atualizado de TODO → TESTED
- [x] Technical review gerado
- [x] Walkthrough gerado
