# Sprint F2-05 — Briefing

**Sprint:** F2-05
**Titulo:** Exportacao Excel/PDF — Folha de Rosto e Quadro-Resumo
**Worker:** kimi-k2.5 (Kimi CLI)
**Status:** TODO
**Data:** 2026-04-26

---

## Objetivo

Disponibilizar exportacao da proposta completa em dois formatos:
- **Excel (xlsx)** com 4 abas: Capa, Quadro-Resumo, CPU, Composicoes — fonte primaria, consumivel pelo Power Query.
- **PDF** com folha de rosto formal (cabecalho do cliente + totais).

Streaming via FastAPI `StreamingResponse`. Frontend ganha botao "Exportar" com menu drop-down em `ProposalDetailPage` e `ProposalCpuPage`.

## Criterios de Aceite

- GET /propostas/{id}/export/excel retorna xlsx com 4 abas (Capa, Quadro-Resumo, CPU, Composicoes)
- GET /propostas/{id}/export/pdf retorna PDF valido (header `%PDF`)
- Headers HTTP com `Content-Disposition: attachment; filename="proposta-{codigo}.xlsx"`
- Frontend tem componente `<ExportMenu />` reutilizado em 2 paginas
- Download dispara via Blob + URL.createObjectURL
- Quadro-Resumo agrega `custo_total_insumo` por `tipo_recurso`
- npx tsc --noEmit sem erros
- python -m pytest backend/tests/ com 130+ PASS, 0 FAIL

## Plano

Arquivo: `docs/sprints/F2-05/plans/2026-04-26-exportacao-excel-pdf.md`

7 tasks:
1. Dependencia reportlab + skeleton do PropostaExportService
2. gerar_excel (4 abas) com openpyxl
3. gerar_pdf (folha de rosto) com reportlab
4. Endpoints GET /export/excel e /export/pdf
5. Frontend proposalsApi exportExcel/exportPdf
6. ExportMenu component
7. Wire em ProposalDetailPage e ProposalCpuPage

## Contexto tecnico

- Service novo: `app/backend/services/proposta_export_service.py`
- Endpoints novos: `app/backend/api/v1/endpoints/proposta_export.py`
- Reutiliza: `PropostaRepository`, `ClienteRepository`, `PropostaItemRepository`, `PropostaItemComposicaoRepository`
- Dep nova: `reportlab>=4.0.0` (adicionar em `app/requirements.txt`)
- Padrao openpyxl: ja usado em `app/backend/services/etl_service.py`
- Frontend: axios `responseType: 'blob'`, padrao MUI `Menu` + `MenuItem`

## Dependencias

- F2-03 TESTED (PqItem com match_status confirmado)
- F2-04 DONE (CPU gerada com composicoes)
- Sem conflito de arquivos com F2-06 e F2-07

## Atencao especial (Kimi)

- `cliente_repo.get_by_id` — verificar se existe; se nao, ler `app/backend/repositories/cliente_repository.py` e adaptar
- `tipo_recurso` em PropostaItemComposicao e enum SQLAlchemy: serializar com `tipo.value if tipo else "OUTRO"`
- Excel deve abrir sem warning no LibreOffice e Excel — testar localmente se possivel
- StreamingResponse precisa de `BytesIO` (nao bytes puros) para o starlette aceitar
