# Worker Prompt — Sprint F2-05

**Para:** Kimi K2.5 (kimi-k2.5)
**Modo:** BUILD / Always Proceed
**Sprint:** F2-05 — Exportacao Excel/PDF (Folha de Rosto e Quadro-Resumo)
**Repo:** C:\Users\rafae\Documents\workspace\github\dinamica-budget

---

Voce e o worker da Sprint F2-05. Implemente o plano completo em `docs/sprints/F2-05/plans/2026-04-26-exportacao-excel-pdf.md` do inicio ao fim sem pausas.

## Por que voce foi escolhido

Esta sprint e backend-pesada: openpyxl multi-aba, reportlab para PDF, StreamingResponse com headers HTTP corretos, e templates determinísticos. Frontend e minimo (1 componente + 2 wires). Sua especialidade em backend Python + libs de IO binario faz match direto com o trabalho.

## Instrucoes de execucao

1. Leia o briefing em `docs/sprints/F2-05/briefing/sprint-F2-05-briefing.md`
2. Leia o plano em `docs/sprints/F2-05/plans/2026-04-26-exportacao-excel-pdf.md`
3. Leia o contexto do codebase listado no plano (especialmente `etl_service.py` para padrao openpyxl)
4. Execute cada task em ordem, fazendo commit apos cada uma
5. Apos cada task de backend: `cd app && python -m pytest backend/tests/ -v --tb=short`
6. Apos cada task de frontend: `cd app/frontend && npx tsc --noEmit`
7. Ao concluir TODAS as tasks: crie
   - `docs/sprints/F2-05/technical-review/technical-review-2026-04-26-f2-05.md`
   - `docs/sprints/F2-05/walkthrough/done/walkthrough-F2-05.md`
   - Atualize status do sprint para TESTED em `docs/shared/governance/BACKLOG.md`

## Atencao especial

- `reportlab>=4.0.0` e dep nova — adicionar em `app/requirements.txt` E garantir `pip install -r app/requirements.txt` antes de rodar testes
- StreamingResponse precisa de `BytesIO`, nao `bytes` puros
- `tipo_recurso.value if tipo_recurso else "OUTRO"` — tipo_recurso e enum SQLAlchemy
- Validar que xlsx gerado abre no LibreOffice/Excel sem warning de corrupcao
- Testes do PDF: validar prefix `b"%PDF"` e `len(raw) > 500` (PDF minimo viavel)

## Criterios de conclusao

- 130+ PASS, 0 FAIL no pytest
- 0 erros no tsc --noEmit
- Todos os 7 tasks com checkbox marcado
- Documentos technical-review e walkthrough criados
- BACKLOG atualizado para TESTED

## Diretorio de trabalho

```
app/requirements.txt
app/backend/services/proposta_export_service.py
app/backend/api/v1/endpoints/proposta_export.py
app/backend/api/v1/router.py
app/backend/tests/unit/test_proposta_export_service.py
app/backend/tests/unit/test_proposta_export_endpoint.py
app/frontend/src/shared/services/api/proposalsApi.ts
app/frontend/src/features/proposals/components/ExportMenu.tsx
app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx
app/frontend/src/features/proposals/pages/ProposalCpuPage.tsx
```

## Commits esperados (sequencia minima)

1. `feat(f2-05): add reportlab dep and PropostaExportService skeleton`
2. `feat(f2-05): implement gerar_excel with 4 sheets (Capa/Resumo/CPU/Composicoes)`
3. `feat(f2-05): implement gerar_pdf folha de rosto with reportlab`
4. `feat(f2-05): add export endpoints with StreamingResponse`
5. `feat(f2-05): add exportExcel/exportPdf to proposalsApi`
6. `feat(f2-05): add ExportMenu component`
7. `feat(f2-05): wire ExportMenu into ProposalDetailPage and ProposalCpuPage`
8. `docs(f2-05): add technical-review and walkthrough, handoff to QA`
