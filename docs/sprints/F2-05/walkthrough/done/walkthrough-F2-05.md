# Walkthrough — Sprint F2-05

**Data:** 2026-04-26
**Sprint:** F2-05 — Exportação Excel/PDF

---

## Como validar

### Backend

1. Certifique-se de que `reportlab>=4.0.0` está instalado:
   ```bash
   cd app && pip install -r requirements.txt
   ```

2. Rode os testes unitários:
   ```bash
   cd app && python -m pytest backend/tests/unit/test_proposta_export_service.py backend/tests/unit/test_proposta_export_endpoint.py -v
   ```

3. Inicie o servidor e teste os endpoints via curl/browser:
   ```
   GET /api/v1/propostas/{id}/export/excel
   GET /api/v1/propostas/{id}/export/pdf
   ```

### Frontend

1. Acesse a página de detalhes de uma proposta (`/propostas/{id}`)
2. Clique em "Exportar" → escolha "Excel (xlsx)" ou "PDF (folha de rosto)"
3. Verifique que o download inicia com nome `proposta-{codigo}.xlsx` ou `.pdf`
4. Repita na página de CPU (`/propostas/{id}/cpu`)

### Critérios de Aceite Verificados

- [x] Excel com 4 abas (Capa, Quadro-Resumo, CPU, Composições)
- [x] PDF válido (header %PDF)
- [x] Headers HTTP com Content-Disposition attachment
- [x] Componente ExportMenu em 2 páginas
- [x] Download via Blob + URL.createObjectURL
- [x] Quadro-Resumo agrega custo_total_insumo por tipo_recurso
- [x] 130+ pytest PASS, 0 FAIL
- [x] 0 erros tsc
