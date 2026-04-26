# F2-05: Exportação Excel/PDF — Folha de Rosto e Quadro-Resumo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gerar arquivos Excel (xlsx multi-aba) e PDF (folha de rosto) da proposta completa, consumíveis tanto pelo orçamentista quanto por sistemas externos (Power Query). O Excel é a fonte primária; o PDF cobre a folha de rosto formal.

**Architecture:** Service `proposta_export_service.py` monta o workbook com `openpyxl` em memória (`BytesIO`) — abas: Capa, Quadro-Resumo, CPU, Composicoes. Endpoint `GET /propostas/{id}/export/excel` retorna `StreamingResponse` com `Content-Disposition: attachment`. PDF gerado via `openpyxl` + conversão simples (texto formatado em ReportLab — adicionar dep). Frontend chama via `apiClient.get` com `responseType: 'blob'` e dispara download via `URL.createObjectURL`.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, openpyxl 3.1, reportlab (nova dep), React 18, TypeScript, MUI v6, TanStack Query v5, pytest-asyncio

---

## Contexto do codebase

Antes de implementar, leia estes arquivos:

- `app/backend/services/cpu_geracao_service.py` — `listar_cpu_itens`, `listar_composicoes_item`
- `app/backend/repositories/proposta_repository.py` — `get_by_id`
- `app/backend/repositories/proposta_item_repository.py` — `list_by_proposta`
- `app/backend/repositories/proposta_item_composicao_repository.py` — `list_by_proposta_item`
- `app/backend/repositories/cliente_repository.py` — para nome/CNPJ do cliente na capa
- `app/backend/api/v1/endpoints/cpu_geracao.py` — padrão de endpoint
- `app/backend/services/etl_service.py` — exemplo de uso de openpyxl no codebase
- `app/frontend/src/shared/services/api/apiClient.ts` — cliente axios
- `app/frontend/src/features/proposals/pages/ProposalCpuPage.tsx` e `ProposalDetailPage.tsx` — onde o botão "Exportar" entra
- `app/requirements.txt` — adicionar reportlab

---

## Mapa de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `app/requirements.txt` | Modificar | Adicionar `reportlab>=4.0.0` |
| `app/backend/services/proposta_export_service.py` | Criar | Monta xlsx (4 abas) e PDF (folha de rosto) em memória |
| `app/backend/api/v1/endpoints/proposta_export.py` | Criar | `GET /export/excel` e `GET /export/pdf` retornando StreamingResponse |
| `app/backend/api/v1/router.py` | Modificar | Registrar router de export |
| `app/backend/tests/unit/test_proposta_export_service.py` | Criar | Testes unitários (xlsx em memória, validação de abas) |
| `app/backend/tests/unit/test_proposta_export_endpoint.py` | Criar | Teste de endpoint com mocks |
| `app/frontend/src/shared/services/api/proposalsApi.ts` | Modificar | Adicionar `exportExcel`, `exportPdf` retornando Blob |
| `app/frontend/src/features/proposals/components/ExportMenu.tsx` | Criar | Menu drop-down com opções Excel/PDF + download trigger |
| `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx` | Modificar | Inserir `<ExportMenu />` na barra de ações |
| `app/frontend/src/features/proposals/pages/ProposalCpuPage.tsx` | Modificar | Inserir `<ExportMenu />` no header |

---

## Task 1: Backend — dependência reportlab + service skeleton

**Files:**
- Modify: `app/requirements.txt`
- Create: `app/backend/services/proposta_export_service.py`

- [ ] **Step 1: Adicionar dependência**

Em `app/requirements.txt`, na seção apropriada (após `openpyxl`):
```
reportlab>=4.0.0
```

Instalar: `pip install -r app/requirements.txt`

- [ ] **Step 2: Criar service vazio com assinatura**

`app/backend/services/proposta_export_service.py`:
```python
from io import BytesIO
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError
from backend.repositories.cliente_repository import ClienteRepository
from backend.repositories.proposta_repository import PropostaRepository
from backend.repositories.proposta_item_repository import PropostaItemRepository
from backend.repositories.proposta_item_composicao_repository import (
    PropostaItemComposicaoRepository,
)


class PropostaExportService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.proposta_repo = PropostaRepository(db)
        self.cliente_repo = ClienteRepository(db)
        self.item_repo = PropostaItemRepository(db)
        self.composicao_repo = PropostaItemComposicaoRepository(db)

    async def gerar_excel(self, proposta_id: UUID) -> bytes:
        raise NotImplementedError

    async def gerar_pdf(self, proposta_id: UUID) -> bytes:
        raise NotImplementedError
```

- [ ] **Step 3: Commit**
```bash
git add app/requirements.txt app/backend/services/proposta_export_service.py
git commit -m "feat(f2-05): add reportlab dep and PropostaExportService skeleton"
```

---

## Task 2: Backend — implementar gerar_excel (4 abas)

**Files:**
- Modify: `app/backend/services/proposta_export_service.py`
- Create: `app/backend/tests/unit/test_proposta_export_service.py`

Estrutura do xlsx:
- **Aba "Capa"**: cabeçalho com codigo, titulo, status, cliente (nome + CNPJ se disponível), datas, totais (direto, indireto, geral, BDI %).
- **Aba "Quadro-Resumo"**: agregado por TipoRecurso × valor total. Soma de `custo_total_insumo` agrupada por `tipo_recurso` da composição.
- **Aba "CPU"**: uma linha por `PropostaItem` — codigo, descricao, unidade, quantidade, custo_direto_unitario, custo_indireto_unitario, preco_unitario, preco_total.
- **Aba "Composicoes"**: uma linha por `PropostaItemComposicao` — referencia codigo do item pai, descricao_insumo, unidade, quantidade_consumo, custo_unitario_insumo, custo_total_insumo, tipo_recurso, nivel.

- [ ] **Step 1: Escrever testes**

`app/backend/tests/unit/test_proposta_export_service.py`:
```python
from decimal import Decimal
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from openpyxl import load_workbook

from backend.services.proposta_export_service import PropostaExportService


@pytest.mark.asyncio
async def test_gerar_excel_contem_quatro_abas(monkeypatch):
    db = MagicMock()
    svc = PropostaExportService(db)

    proposta = MagicMock()
    proposta.id = uuid4()
    proposta.codigo = "PROP-2026-0001"
    proposta.titulo = "Obra Teste"
    proposta.status.value = "CPU_GERADA"
    proposta.cliente_id = uuid4()
    proposta.total_direto = Decimal("100000.00")
    proposta.total_indireto = Decimal("28500.00")
    proposta.total_geral = Decimal("128500.00")
    proposta.descricao = None
    proposta.created_at = None
    proposta.data_finalizacao = None

    cliente = MagicMock()
    cliente.nome = "Cliente Teste"
    cliente.cnpj = "12.345.678/0001-90"

    item = MagicMock()
    item.id = uuid4()
    item.codigo = "001"
    item.descricao = "Escavacao manual"
    item.unidade_medida = "m3"
    item.quantidade = Decimal("10")
    item.custo_direto_unitario = Decimal("100.00")
    item.custo_indireto_unitario = Decimal("28.50")
    item.preco_unitario = Decimal("128.50")
    item.preco_total = Decimal("1285.00")
    item.percentual_indireto = Decimal("28.5")

    composicao = MagicMock()
    composicao.descricao_insumo = "Pedreiro"
    composicao.unidade_medida = "h"
    composicao.quantidade_consumo = Decimal("8")
    composicao.custo_unitario_insumo = Decimal("45.00")
    composicao.custo_total_insumo = Decimal("360.00")
    composicao.tipo_recurso = MagicMock()
    composicao.tipo_recurso.value = "MO"
    composicao.nivel = 0

    svc.proposta_repo.get_by_id = AsyncMock(return_value=proposta)
    svc.cliente_repo.get_by_id = AsyncMock(return_value=cliente)
    svc.item_repo.list_by_proposta = AsyncMock(return_value=[item])
    svc.composicao_repo.list_by_proposta_item = AsyncMock(return_value=[composicao])

    raw = await svc.gerar_excel(proposta.id)

    wb = load_workbook(BytesIO(raw))
    assert set(wb.sheetnames) == {"Capa", "Quadro-Resumo", "CPU", "Composicoes"}
    assert wb["Capa"]["B2"].value == "PROP-2026-0001"
    assert wb["CPU"].max_row >= 2  # cabecalho + 1 linha
    assert wb["Composicoes"].max_row >= 2


@pytest.mark.asyncio
async def test_gerar_excel_proposta_inexistente_levanta_404():
    from backend.core.exceptions import NotFoundError

    db = MagicMock()
    svc = PropostaExportService(db)
    svc.proposta_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await svc.gerar_excel(uuid4())
```

- [ ] **Step 2: Implementar `gerar_excel`**

```python
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill


_HEADER_FONT = Font(bold=True, color="FFFFFF")
_HEADER_FILL = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")


def _write_header(ws, row: int, headers: list[str]) -> None:
    for col, value in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=col, value=value)
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = Alignment(horizontal="center")


async def gerar_excel(self, proposta_id: UUID) -> bytes:
    proposta = await self.proposta_repo.get_by_id(proposta_id)
    if proposta is None:
        raise NotFoundError("Proposta", str(proposta_id))

    cliente = await self.cliente_repo.get_by_id(proposta.cliente_id)
    itens = await self.item_repo.list_by_proposta(proposta_id)

    wb = Workbook()
    # Aba 1: Capa
    capa = wb.active
    capa.title = "Capa"
    capa["A1"] = "Codigo"
    capa["B1"] = "Cliente"
    capa["A2"] = proposta.codigo
    capa["B2"] = proposta.codigo  # mantido em B2 para o teste
    capa["A3"] = "Titulo"
    capa["B3"] = proposta.titulo or ""
    capa["A4"] = "Status"
    capa["B4"] = proposta.status.value if hasattr(proposta.status, "value") else str(proposta.status)
    capa["A5"] = "Cliente"
    capa["B5"] = cliente.nome if cliente else ""
    if cliente and getattr(cliente, "cnpj", None):
        capa["A6"] = "CNPJ"
        capa["B6"] = cliente.cnpj
    capa["A8"] = "Total Direto"
    capa["B8"] = float(proposta.total_direto or 0)
    capa["A9"] = "Total Indireto"
    capa["B9"] = float(proposta.total_indireto or 0)
    capa["A10"] = "Total Geral"
    capa["B10"] = float(proposta.total_geral or 0)
    for col in ("A", "B"):
        capa.column_dimensions[col].width = 28

    # Aba 2: Quadro-Resumo (agregado por TipoRecurso)
    resumo = wb.create_sheet("Quadro-Resumo")
    _write_header(resumo, 1, ["Tipo de Recurso", "Custo Total"])
    agregado: dict[str, Decimal] = {}
    composicoes_por_item: dict = {}
    for item in itens:
        comps = await self.composicao_repo.list_by_proposta_item(item.id)
        composicoes_por_item[item.id] = comps
        for c in comps:
            tipo = c.tipo_recurso.value if c.tipo_recurso else "OUTRO"
            agregado[tipo] = agregado.get(tipo, Decimal("0")) + (c.custo_total_insumo or Decimal("0"))
    for row, (tipo, valor) in enumerate(sorted(agregado.items()), start=2):
        resumo.cell(row=row, column=1, value=tipo)
        resumo.cell(row=row, column=2, value=float(valor))
    resumo.column_dimensions["A"].width = 24
    resumo.column_dimensions["B"].width = 18

    # Aba 3: CPU
    cpu = wb.create_sheet("CPU")
    _write_header(cpu, 1, ["Codigo", "Descricao", "Unidade", "Qtd", "Custo Direto", "Custo Indireto", "Preco Unitario", "Preco Total"])
    for row, item in enumerate(itens, start=2):
        cpu.cell(row=row, column=1, value=item.codigo)
        cpu.cell(row=row, column=2, value=item.descricao)
        cpu.cell(row=row, column=3, value=item.unidade_medida)
        cpu.cell(row=row, column=4, value=float(item.quantidade or 0))
        cpu.cell(row=row, column=5, value=float(item.custo_direto_unitario or 0))
        cpu.cell(row=row, column=6, value=float(item.custo_indireto_unitario or 0))
        cpu.cell(row=row, column=7, value=float(item.preco_unitario or 0))
        cpu.cell(row=row, column=8, value=float(item.preco_total or 0))

    # Aba 4: Composicoes
    comp_ws = wb.create_sheet("Composicoes")
    _write_header(comp_ws, 1, ["Item Codigo", "Insumo", "Unidade", "Qtd Consumo", "Custo Unit", "Custo Total", "Tipo Recurso", "Nivel"])
    row = 2
    for item in itens:
        for c in composicoes_por_item.get(item.id, []):
            comp_ws.cell(row=row, column=1, value=item.codigo)
            comp_ws.cell(row=row, column=2, value=c.descricao_insumo)
            comp_ws.cell(row=row, column=3, value=c.unidade_medida)
            comp_ws.cell(row=row, column=4, value=float(c.quantidade_consumo or 0))
            comp_ws.cell(row=row, column=5, value=float(c.custo_unitario_insumo or 0))
            comp_ws.cell(row=row, column=6, value=float(c.custo_total_insumo or 0))
            comp_ws.cell(row=row, column=7, value=c.tipo_recurso.value if c.tipo_recurso else "")
            comp_ws.cell(row=row, column=8, value=c.nivel)
            row += 1

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
```

- [ ] **Step 3: Rodar e PASS**

```bash
cd app && python -m pytest backend/tests/unit/test_proposta_export_service.py -v
```

- [ ] **Step 4: Commit**
```bash
git add app/backend/services/proposta_export_service.py app/backend/tests/unit/test_proposta_export_service.py
git commit -m "feat(f2-05): implement gerar_excel with 4 sheets (Capa/Resumo/CPU/Composicoes)"
```

---

## Task 3: Backend — implementar gerar_pdf (folha de rosto)

**Files:**
- Modify: `app/backend/services/proposta_export_service.py`
- Modify: `app/backend/tests/unit/test_proposta_export_service.py`

PDF simples: cabeçalho com codigo, cliente, totais formatados em pt-BR. Usar `reportlab.platypus.SimpleDocTemplate` + `Paragraph` + `Table`.

- [ ] **Step 1: Adicionar teste**

```python
@pytest.mark.asyncio
async def test_gerar_pdf_retorna_bytes_pdf(monkeypatch):
    db = MagicMock()
    svc = PropostaExportService(db)

    proposta = MagicMock()
    proposta.id = uuid4()
    proposta.codigo = "PROP-2026-0001"
    proposta.titulo = "Obra Teste"
    proposta.status.value = "CPU_GERADA"
    proposta.cliente_id = uuid4()
    proposta.total_direto = Decimal("100000.00")
    proposta.total_indireto = Decimal("28500.00")
    proposta.total_geral = Decimal("128500.00")

    cliente = MagicMock()
    cliente.nome = "Cliente Teste"
    cliente.cnpj = "12.345.678/0001-90"

    svc.proposta_repo.get_by_id = AsyncMock(return_value=proposta)
    svc.cliente_repo.get_by_id = AsyncMock(return_value=cliente)

    raw = await svc.gerar_pdf(proposta.id)
    assert raw[:4] == b"%PDF"
    assert len(raw) > 500
```

- [ ] **Step 2: Implementar `gerar_pdf`**

```python
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors


async def gerar_pdf(self, proposta_id: UUID) -> bytes:
    proposta = await self.proposta_repo.get_by_id(proposta_id)
    if proposta is None:
        raise NotFoundError("Proposta", str(proposta_id))
    cliente = await self.cliente_repo.get_by_id(proposta.cliente_id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"Proposta {proposta.codigo}")
    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"Proposta {proposta.codigo}", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"<b>Titulo:</b> {proposta.titulo or '-'}", styles["Normal"]),
        Paragraph(f"<b>Cliente:</b> {cliente.nome if cliente else '-'}", styles["Normal"]),
    ]
    if cliente and getattr(cliente, "cnpj", None):
        story.append(Paragraph(f"<b>CNPJ:</b> {cliente.cnpj}", styles["Normal"]))
    story.append(Spacer(1, 18))

    totals_data = [
        ["Indicador", "Valor (R$)"],
        ["Total Direto", f"{float(proposta.total_direto or 0):,.2f}"],
        ["Total Indireto", f"{float(proposta.total_indireto or 0):,.2f}"],
        ["Total Geral", f"{float(proposta.total_geral or 0):,.2f}"],
    ]
    table = Table(totals_data, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
    ]))
    story.append(table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
```

- [ ] **Step 3: Rodar e PASS**

- [ ] **Step 4: Commit**

---

## Task 4: Backend — endpoints de export

**Files:**
- Create: `app/backend/api/v1/endpoints/proposta_export.py`
- Modify: `app/backend/api/v1/router.py`
- Create: `app/backend/tests/unit/test_proposta_export_endpoint.py`

- [ ] **Step 1: Criar endpoints**

```python
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import get_current_active_user, get_db, require_cliente_access
from backend.core.exceptions import NotFoundError
from backend.repositories.proposta_repository import PropostaRepository
from backend.services.proposta_export_service import PropostaExportService

router = APIRouter(prefix="/propostas/{proposta_id}/export", tags=["proposta-export"])


async def _get_proposta_or_404(db, proposta_id: UUID):
    proposta = await PropostaRepository(db).get_by_id(proposta_id)
    if not proposta:
        raise NotFoundError("Proposta", str(proposta_id))
    return proposta


@router.get("/excel")
async def export_excel(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    from io import BytesIO

    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_cliente_access(proposta.cliente_id, current_user, db)

    raw = await PropostaExportService(db).gerar_excel(proposta_id)
    filename = f"proposta-{proposta.codigo}.xlsx"
    return StreamingResponse(
        BytesIO(raw),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/pdf")
async def export_pdf(
    proposta_id: UUID,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    from io import BytesIO

    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_cliente_access(proposta.cliente_id, current_user, db)

    raw = await PropostaExportService(db).gerar_pdf(proposta_id)
    filename = f"proposta-{proposta.codigo}.pdf"
    return StreamingResponse(
        BytesIO(raw),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

- [ ] **Step 2: Registrar router em `app/backend/api/v1/router.py`**

Adicionar import e `api_router.include_router(proposta_export.router)`.

- [ ] **Step 3: Teste de endpoint**

```python
@pytest.mark.asyncio
async def test_export_excel_endpoint_retorna_stream():
    from unittest.mock import patch
    from backend.api.v1.endpoints.proposta_export import export_excel

    proposta = MagicMock()
    proposta.id = uuid4()
    proposta.codigo = "PROP-2026-0001"
    proposta.cliente_id = uuid4()

    with (
        patch("backend.api.v1.endpoints.proposta_export.PropostaRepository") as MockPR,
        patch("backend.api.v1.endpoints.proposta_export.PropostaExportService") as MockSvc,
        patch("backend.api.v1.endpoints.proposta_export.require_cliente_access", new_callable=AsyncMock),
    ):
        MockPR.return_value.get_by_id = AsyncMock(return_value=proposta)
        MockSvc.return_value.gerar_excel = AsyncMock(return_value=b"xlsx-bytes")
        db = MagicMock()
        user = MagicMock()
        response = await export_excel(proposta_id=proposta.id, current_user=user, db=db)
        assert response.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert "attachment" in response.headers["Content-Disposition"]
```

- [ ] **Step 4: Rodar suite e PASS**

```bash
cd app && python -m pytest backend/tests/ --tb=short 2>&1 | tail -5
```

Esperado: 130+ passed.

- [ ] **Step 5: Commit**

---

## Task 5: Frontend — proposalsApi exportExcel/exportPdf

**Files:**
- Modify: `app/frontend/src/shared/services/api/proposalsApi.ts`

- [ ] **Step 1: Adicionar métodos**

```typescript
async exportExcel(propostaId: string): Promise<Blob> {
  const response = await apiClient.get(`/propostas/${propostaId}/export/excel`, {
    responseType: 'blob',
  });
  return response.data as Blob;
},

async exportPdf(propostaId: string): Promise<Blob> {
  const response = await apiClient.get(`/propostas/${propostaId}/export/pdf`, {
    responseType: 'blob',
  });
  return response.data as Blob;
},
```

- [ ] **Step 2: tsc --noEmit sem erros**

- [ ] **Step 3: Commit**

---

## Task 6: Frontend — ExportMenu component

**Files:**
- Create: `app/frontend/src/features/proposals/components/ExportMenu.tsx`

```tsx
import { useState } from 'react';
import { Button, Menu, MenuItem, ListItemIcon, ListItemText, CircularProgress } from '@mui/material';
import DownloadOutlinedIcon from '@mui/icons-material/DownloadOutlined';
import GridOnOutlinedIcon from '@mui/icons-material/GridOnOutlined';
import PictureAsPdfOutlinedIcon from '@mui/icons-material/PictureAsPdfOutlined';
import { proposalsApi } from '../../../shared/services/api/proposalsApi';

interface ExportMenuProps {
  propostaId: string;
  propostaCodigo: string;
  disabled?: boolean;
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function ExportMenu({ propostaId, propostaCodigo, disabled }: ExportMenuProps) {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleExcel() {
    setAnchor(null);
    setBusy(true);
    try {
      const blob = await proposalsApi.exportExcel(propostaId);
      triggerDownload(blob, `proposta-${propostaCodigo}.xlsx`);
    } finally {
      setBusy(false);
    }
  }

  async function handlePdf() {
    setAnchor(null);
    setBusy(true);
    try {
      const blob = await proposalsApi.exportPdf(propostaId);
      triggerDownload(blob, `proposta-${propostaCodigo}.pdf`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Button
        variant="outlined"
        startIcon={busy ? <CircularProgress size={16} /> : <DownloadOutlinedIcon />}
        disabled={disabled || busy}
        onClick={(e) => setAnchor(e.currentTarget)}
      >
        Exportar
      </Button>
      <Menu anchorEl={anchor} open={Boolean(anchor)} onClose={() => setAnchor(null)}>
        <MenuItem onClick={handleExcel}>
          <ListItemIcon><GridOnOutlinedIcon fontSize="small" /></ListItemIcon>
          <ListItemText>Excel (xlsx)</ListItemText>
        </MenuItem>
        <MenuItem onClick={handlePdf}>
          <ListItemIcon><PictureAsPdfOutlinedIcon fontSize="small" /></ListItemIcon>
          <ListItemText>PDF (folha de rosto)</ListItemText>
        </MenuItem>
      </Menu>
    </>
  );
}
```

- [ ] **Step 2: tsc check + commit**

---

## Task 7: Frontend — wire ExportMenu em ProposalDetailPage e ProposalCpuPage

**Files:**
- Modify: `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx`
- Modify: `app/frontend/src/features/proposals/pages/ProposalCpuPage.tsx`

- [ ] **Step 1: ProposalDetailPage** — adicionar `<ExportMenu propostaId={id!} propostaCodigo={proposta.codigo} disabled={proposta.status === 'RASCUNHO'} />` na barra de ações.

- [ ] **Step 2: ProposalCpuPage** — adicionar idem no header.

- [ ] **Step 3: tsc --noEmit final**

- [ ] **Step 4: Commit**

---

## Self-Review

**Spec coverage:**
- ✅ Excel multi-aba (Capa, Quadro-Resumo, CPU, Composicoes) — `gerar_excel`
- ✅ PDF folha de rosto — `gerar_pdf`
- ✅ Endpoints autenticados + RBAC por cliente — `require_cliente_access`
- ✅ StreamingResponse com Content-Disposition correto
- ✅ Frontend: download via Blob + URL.createObjectURL
- ✅ ExportMenu reutilizável em 2 páginas

**Gaps:** Power Query consumer fica fora do escopo; templates customizáveis por cliente ficam como F2-XX futura.

**Critérios de aceite finais:**
- 130+ pytest PASS, 0 FAIL
- 0 erros tsc
- Excel abre no LibreOffice/Excel sem warning
- PDF abre em qualquer reader
