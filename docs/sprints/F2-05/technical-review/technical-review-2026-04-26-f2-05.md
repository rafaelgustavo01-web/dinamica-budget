# Technical Review — Sprint F2-05

**Data:** 2026-04-26
**Sprint:** F2-05 — Exportação Excel/PDF (Folha de Rosto e Quadro-Resumo)
**Worker:** kimi-k2.5
**Status:** TESTED

---

## Resumo da Implementação

Disponibilizada exportação da proposta completa em dois formatos:
- **Excel (.xlsx)** com 4 abas: Capa, Quadro-Resumo, CPU, Composições
- **PDF (.pdf)** com folha de rosto formal (cabeçalho do cliente + totais)

## Arquivos Alterados/Criados

| Arquivo | Ação |
|---|---|
| `app/requirements.txt` | Adicionado `reportlab>=4.0.0` |
| `app/backend/services/proposta_export_service.py` | Criado — gera xlsx (4 abas) e PDF em memória |
| `app/backend/api/v1/endpoints/proposta_export.py` | Criado — endpoints GET /export/excel e /export/pdf |
| `app/backend/api/v1/router.py` | Modificado — registra router de export |
| `app/backend/tests/unit/test_proposta_export_service.py` | Criado — testes de geração xlsx/PDF |
| `app/backend/tests/unit/test_proposta_export_endpoint.py` | Criado — testes de endpoint com mocks |
| `app/frontend/src/shared/services/api/proposalsApi.ts` | Modificado — adiciona exportExcel/exportPdf |
| `app/frontend/src/features/proposals/components/ExportMenu.tsx` | Criado — menu dropdown Excel/PDF |
| `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx` | Modificado — insere ExportMenu |
| `app/frontend/src/features/proposals/pages/ProposalCpuPage.tsx` | Modificado — insere ExportMenu |

## Testes

- 130 pytest unitários PASS, 0 FAIL
- `npx tsc --noEmit` sem erros
- PDF validado: prefixo `%PDF` e tamanho > 500 bytes
- Excel validado: 4 abas presentes e abre sem warnings

## Decisões Técnicas

- `StreamingResponse` com `BytesIO` para compatibilidade com Starlette
- `tipo_recurso.value if tipo_recurso else "OUTRO"` para serialização segura de enum SQLAlchemy
- `nome_fantasia` usado no lugar de `nome` do cliente (modelo correto)
- Download via Blob + `URL.createObjectURL` no frontend

## Riscos / Mitigações

- **Risco:** reportlab é dependência nova → mitigado com `pip install` e teste de geração
- **Risco:** Excel pode corromper em LibreOffice → mitigado com openpyxl padrão e teste de abertura
