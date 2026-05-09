# Technical Review — F4-03 — 2026-05-08

> Sprint: F4-03 — BASES/BCUs Upload Individual + CRUD
> Worker: Opencode (frontend/UX substituto)
> Backlog status on exit: TESTED

## Component Map

| File | Responsibility | Change in this sprint |
|------|----------------|-----------------------|
| `app/frontend/src/shared/services/api/bcuItemApi.ts` | Contratos TS para upload individual e CRUD de itens BCU | Created |
| `app/frontend/src/features/bcu/BcuUploadPage.tsx` | Tela de upload individual com preview/validação (xlsx parse) | Created |
| `app/frontend/src/features/bcu/BcuItemDialog.tsx` | Modal genérico de CRUD para todos os tipos de item BCU | Created |
| `app/frontend/src/features/bcu/BcuPage.tsx` | Visualização BCU + ações CRUD inline (editar/excluir/novo) | Modified |
| `app/frontend/src/features/bcu/BcuGestaoPage.tsx` | Gestão de versões BCU (upload completo, ativar, deletar) | Created (pré-existente, untracked) |
| `app/frontend/src/app/router.tsx` | Rotas para /bcu/gestao e /bcu/upload | Modified |
| `app/frontend/src/shared/components/layout/navigationConfig.tsx` | Itens de menu Gestão da Base e Upload Individual | Modified |
| `app/backend/api/v1/endpoints/bcu.py` | Endpoint DELETE /bcu/cabecalhos/{id} | Modified (pré-existente) |
| `app/frontend/package.json` | Dependência xlsx para parse no frontend | Modified |

## Delivery Summary

- Planned change: completar/revisar frontend para upload individual + CRUD BASE/BCU.
- Delivered change:
  - Contratos TypeScript definidos para 12 endpoints de CRUD (criar/atualizar/deletar) por tipo de item e 1 endpoint de upload individual.
  - Tela de upload individual com parse de XLSX no frontend, preview de 20 linhas e validação de colunas obrigatórias por tipo.
  - CRUD inline em todas as 6 abas do BcuPage (Mão de Obra, Equipamentos, Encargos, EPI, Ferramentas, Mobilização).
  - Roteamento e navegação para Gestão da Base e Upload Individual.
- Known risk: backend não implementou os endpoints de upload individual nem CRUD de itens. O frontend detecta 404/Not Found e exibe mensagem amigável indicando que o endpoint está pendente.

## Validation Snapshot

```bash
cd app/frontend && npm run build
```

- Result: pass
- Notes: build TypeScript + Vite concluído sem erros. Chunk BcuUploadPage ~339KB (xlsx parser incluído).

```bash
git diff --check
```

- Result: pass (excluindo package-lock.json gerado pelo npm)

## Follow-on Notes for QA

- Os contratos TS em `bcuItemApi.ts` servem como especificação para o backend implementar:
  - POST/PATCH/DELETE `/bcu/{cabecalho_id}/mao-obra` (e equivalentes para equipamentos, encargos, epi, ferramentas, mobilizacao)
  - POST `/bcu/importar-individual` (upload de planilha única por tabela)
- O endpoint DELETE `/bcu/cabecalhos/{id}` já existe no backend e é consumido pela Gestão da Base.
- Upload individual está marcado como `status: partial` na navegação até o backend entregar os endpoints.
