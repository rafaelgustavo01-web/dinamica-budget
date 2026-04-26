# F2-03: Tela de Revisão de Match Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir o match totalmente automático por uma tela onde o orçamentista revisa cada sugestão e confirma, substitui ou rejeita manualmente antes de gerar a CPU.

**Architecture:** Backend expõe dois endpoints novos no router `/propostas/{id}/pq`: `GET /itens` (lista PqItems com paginação e filtro por status) e `PATCH /itens/{item_id}/match` (ação: confirmar/substituir/rejeitar). O frontend adiciona a página `MatchReviewPage` com tabela de revisão, barra de progresso e diálogo de busca para substituição. Todas as pages de proposta existentes recebem botão de acesso à revisão quando há itens em `SUGERIDO`.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, Pydantic v2, React 18, TypeScript, MUI v6, TanStack Query v5, pytest-asyncio

---

## Mapa de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `app/backend/schemas/proposta.py` | Modificar | Adicionar `PqItemResponse`, `PqMatchConfirmarRequest` |
| `app/backend/repositories/pq_item_repository.py` | Modificar | Adicionar `confirmar_match_status` |
| `app/backend/api/v1/endpoints/pq_importacao.py` | Modificar | Adicionar GET `/itens` e PATCH `/itens/{item_id}/match` |
| `app/backend/tests/unit/test_pq_match_review.py` | Criar | Testes unitários dos 2 novos endpoints |
| `app/frontend/src/shared/services/api/proposalsApi.ts` | Modificar | Tipos + `listPqItens`, `confirmarMatch` |
| `app/frontend/src/features/proposals/pages/MatchReviewPage.tsx` | Criar | Página principal de revisão |
| `app/frontend/src/features/proposals/components/MatchItemRow.tsx` | Criar | Linha de tabela com ações por item |
| `app/frontend/src/features/proposals/components/ServicoPickerDialog.tsx` | Criar | Diálogo de busca para substituição |
| `app/frontend/src/features/proposals/routes.tsx` | Modificar | Adicionar rota `/propostas/:id/match-review` |
| `app/frontend/src/features/proposals/pages/ProposalImportPage.tsx` | Modificar | Botão "Revisar Match" após match bem-sucedido |
| `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx` | Modificar | Botão "Revisar Match" na barra de ações |

---

## Task 1: Backend — schemas PqItemResponse e PqMatchConfirmarRequest

**Files:**
- Modify: `app/backend/schemas/proposta.py` (após linha 97, ao final do arquivo)

- [ ] **Step 1: Escrever o teste que falha**

Crie `app/backend/tests/unit/test_pq_match_review.py`:

```python
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.models.enums import StatusMatch, TipoServicoMatch
from backend.models.proposta import PqItem
from backend.schemas.proposta import PqItemResponse, PqMatchConfirmarRequest


def _make_pq_item(**kwargs) -> PqItem:
    item = MagicMock(spec=PqItem)
    item.id = kwargs.get("id", uuid4())
    item.proposta_id = kwargs.get("proposta_id", uuid4())
    item.pq_importacao_id = None
    item.codigo_original = kwargs.get("codigo_original", "001")
    item.descricao_original = kwargs.get("descricao_original", "Escavacao manual")
    item.unidade_medida_original = kwargs.get("unidade_medida_original", "m3")
    item.quantidade_original = kwargs.get("quantidade_original", Decimal("10"))
    item.match_status = kwargs.get("match_status", StatusMatch.SUGERIDO)
    item.match_confidence = kwargs.get("match_confidence", Decimal("0.92"))
    item.servico_match_id = kwargs.get("servico_match_id", uuid4())
    item.servico_match_tipo = kwargs.get("servico_match_tipo", TipoServicoMatch.BASE_TCPO)
    item.linha_planilha = kwargs.get("linha_planilha", 2)
    item.observacao = None
    from datetime import datetime, timezone
    item.created_at = datetime.now(timezone.utc)
    item.updated_at = datetime.now(timezone.utc)
    return item


def test_pq_item_response_schema_from_model():
    item = _make_pq_item()
    response = PqItemResponse.model_validate(item)
    assert response.descricao_original == "Escavacao manual"
    assert response.match_status == StatusMatch.SUGERIDO
    assert response.match_confidence == Decimal("0.92")


def test_pq_match_confirmar_request_confirmar():
    req = PqMatchConfirmarRequest(acao="confirmar")
    assert req.acao == "confirmar"
    assert req.servico_match_id is None


def test_pq_match_confirmar_request_rejeitar():
    req = PqMatchConfirmarRequest(acao="rejeitar")
    assert req.acao == "rejeitar"


def test_pq_match_confirmar_request_substituir_requer_servico_id():
    import pytest
    from pydantic import ValidationError as PydanticValidationError
    with pytest.raises(PydanticValidationError):
        PqMatchConfirmarRequest(
            acao="substituir",
            # servico_match_id ausente — deve falhar
        )
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

```bash
cd app && python -m pytest backend/tests/unit/test_pq_match_review.py -v
```
Esperado: `ImportError` ou `ValidationError` — `PqItemResponse` e `PqMatchConfirmarRequest` ainda não existem.

- [ ] **Step 3: Implementar os schemas**

No final de `app/backend/schemas/proposta.py`, adicionar:

```python
from typing import Literal


class PqItemResponse(BaseModel):
    id: UUID
    proposta_id: UUID
    pq_importacao_id: UUID | None
    codigo_original: str | None
    descricao_original: str
    unidade_medida_original: str | None
    quantidade_original: Decimal | None
    match_status: StatusMatch
    match_confidence: Decimal | None
    servico_match_id: UUID | None
    servico_match_tipo: TipoServicoMatch | None
    linha_planilha: int | None
    observacao: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PqMatchConfirmarRequest(BaseModel):
    acao: Literal["confirmar", "substituir", "rejeitar"]
    servico_match_id: UUID | None = None
    servico_match_tipo: TipoServicoMatch | None = None
    quantidade: Decimal | None = None

    @field_validator("servico_match_id")
    @classmethod
    def substituir_requer_servico(cls, v: UUID | None, info) -> UUID | None:
        if info.data.get("acao") == "substituir" and v is None:
            raise ValueError("servico_match_id e obrigatorio para acao=substituir")
        return v
```

O import de `StatusMatch` e `TipoServicoMatch` já existe na linha 7 de `proposta.py`. Adicionar `Literal` ao import do `typing` (linha 5):

```python
from typing import Literal
```

E adicionar `field_validator` ao import do pydantic:
```python
from pydantic import BaseModel, ConfigDict, Field, field_validator
```

- [ ] **Step 4: Rodar os testes e confirmar PASS**

```bash
cd app && python -m pytest backend/tests/unit/test_pq_match_review.py -v
```
Esperado: 4 PASS.

- [ ] **Step 5: Commit**

```bash
git add app/backend/schemas/proposta.py app/backend/tests/unit/test_pq_match_review.py
git commit -m "feat(f2-03): add PqItemResponse and PqMatchConfirmarRequest schemas"
```

---

## Task 2: Backend — GET /pq/itens + PATCH /pq/itens/{item_id}/match

**Files:**
- Modify: `app/backend/api/v1/endpoints/pq_importacao.py`
- Modify: `app/backend/tests/unit/test_pq_match_review.py`

- [ ] **Step 1: Escrever testes dos endpoints**

Adicionar ao final de `app/backend/tests/unit/test_pq_match_review.py`:

```python
@pytest.mark.asyncio
async def test_listar_pq_itens_retorna_lista():
    from unittest.mock import patch
    from backend.api.v1.endpoints.pq_importacao import listar_pq_itens

    item = _make_pq_item()
    proposta = MagicMock()
    proposta.cliente_id = uuid4()

    with (
        patch("backend.api.v1.endpoints.pq_importacao.PropostaRepository") as MockPR,
        patch("backend.api.v1.endpoints.pq_importacao.PqItemRepository") as MockIR,
        patch("backend.api.v1.endpoints.pq_importacao.require_cliente_access", new_callable=AsyncMock),
    ):
        MockPR.return_value.get_by_id = AsyncMock(return_value=proposta)
        MockIR.return_value.list_by_proposta = AsyncMock(return_value=[item])
        db = MagicMock()
        user = MagicMock()
        result = await listar_pq_itens(proposta_id=proposta.id, status_match=None, current_user=user, db=db)
        assert len(result) == 1
        assert result[0].descricao_original == "Escavacao manual"


@pytest.mark.asyncio
async def test_atualizar_match_confirmar():
    from unittest.mock import patch
    from backend.api.v1.endpoints.pq_importacao import atualizar_match_item
    from backend.schemas.proposta import PqMatchConfirmarRequest

    item = _make_pq_item()
    proposta = MagicMock()
    proposta.id = item.proposta_id
    proposta.cliente_id = uuid4()

    with (
        patch("backend.api.v1.endpoints.pq_importacao.PropostaRepository") as MockPR,
        patch("backend.api.v1.endpoints.pq_importacao.PqItemRepository") as MockIR,
        patch("backend.api.v1.endpoints.pq_importacao.require_cliente_access", new_callable=AsyncMock),
    ):
        MockPR.return_value.get_by_id = AsyncMock(return_value=proposta)
        MockIR.return_value.get_by_id = AsyncMock(return_value=item)
        MockIR.return_value.update_status = AsyncMock()
        db = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        user = MagicMock()
        req = PqMatchConfirmarRequest(acao="confirmar")
        result = await atualizar_match_item(
            proposta_id=proposta.id,
            item_id=item.id,
            body=req,
            current_user=user,
            db=db,
        )
        assert result is not None
```

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
cd app && python -m pytest backend/tests/unit/test_pq_match_review.py::test_listar_pq_itens_retorna_lista -v
```
Esperado: `ImportError` — `listar_pq_itens` ainda não existe.

- [ ] **Step 3: Implementar os 2 endpoints em pq_importacao.py**

Adicionar imports no topo de `app/backend/api/v1/endpoints/pq_importacao.py`:
```python
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from backend.models.enums import StatusMatch
from backend.schemas.proposta import (
    PqImportacaoResponse,
    PqItemResponse,
    PqMatchConfirmarRequest,
    PqMatchResponse,
)
```

Adicionar ao final do arquivo (após `executar_match`):

```python
@router.get("/itens", response_model=list[PqItemResponse])
async def listar_pq_itens(
    proposta_id: UUID,
    status_match: StatusMatch | None = Query(default=None),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PqItemResponse]:
    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_cliente_access(proposta.cliente_id, current_user, db)
    items = await PqItemRepository(db).list_by_proposta(proposta_id, status_match=status_match)
    return [PqItemResponse.model_validate(item) for item in items]


@router.patch("/itens/{item_id}/match", response_model=PqItemResponse)
async def atualizar_match_item(
    proposta_id: UUID,
    item_id: UUID,
    body: PqMatchConfirmarRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> PqItemResponse:
    from backend.core.exceptions import NotFoundError, ValidationError as AppValidationError
    proposta = await _get_proposta_or_404(db, proposta_id)
    await require_cliente_access(proposta.cliente_id, current_user, db)

    repo = PqItemRepository(db)
    item = await repo.get_by_id(item_id)
    if item is None or item.proposta_id != proposta_id:
        raise NotFoundError("PqItem", str(item_id))

    if body.acao == "rejeitar":
        await repo.update_status(item, StatusMatch.SEM_MATCH)
    elif body.acao == "confirmar":
        await repo.update_status(item, StatusMatch.CONFIRMADO)
    elif body.acao == "substituir":
        if body.servico_match_id is None or body.servico_match_tipo is None:
            raise AppValidationError("servico_match_id e servico_match_tipo sao obrigatorios para acao=substituir")
        await repo.update_match(
            pq_item=item,
            servico_match_id=body.servico_match_id,
            servico_match_tipo=body.servico_match_tipo,
            confidence=1.0,
        )
        await repo.update_status(item, StatusMatch.MANUAL)

    if body.quantidade is not None:
        item.quantidade_original = body.quantidade
        await db.flush()

    await db.commit()
    await db.refresh(item)
    return PqItemResponse.model_validate(item)
```

- [ ] **Step 4: Rodar suite completa**

```bash
cd app && python -m pytest backend/tests/unit/test_pq_match_review.py -v
```
Esperado: todos os testes PASS.

- [ ] **Step 5: Rodar suite de regressão**

```bash
cd app && python -m pytest backend/tests/ -v --tb=short 2>&1 | tail -5
```
Esperado: 110+ passed, 0 failed.

- [ ] **Step 6: Commit**

```bash
git add app/backend/api/v1/endpoints/pq_importacao.py app/backend/tests/unit/test_pq_match_review.py
git commit -m "feat(f2-03): add GET /pq/itens and PATCH /pq/itens/{id}/match endpoints"
```

---

## Task 3: Frontend — tipos e métodos na proposalsApi

**Files:**
- Modify: `app/frontend/src/shared/services/api/proposalsApi.ts`

- [ ] **Step 1: Adicionar tipos TypeScript**

Após a interface `PqMatchResponse` (linha 53) em `proposalsApi.ts`, inserir:

```typescript
export type StatusMatch =
  | 'PENDENTE'
  | 'BUSCANDO'
  | 'SUGERIDO'
  | 'CONFIRMADO'
  | 'MANUAL'
  | 'SEM_MATCH';

export type TipoServicoMatch = 'ITEM_PROPRIO' | 'BASE_TCPO';

export type AcaoMatch = 'confirmar' | 'substituir' | 'rejeitar';

export interface PqItemResponse {
  id: string;
  proposta_id: string;
  pq_importacao_id: string | null;
  codigo_original: string | null;
  descricao_original: string;
  unidade_medida_original: string | null;
  quantidade_original: string | null;
  match_status: StatusMatch;
  match_confidence: string | null;
  servico_match_id: string | null;
  servico_match_tipo: TipoServicoMatch | null;
  linha_planilha: number | null;
  observacao: string | null;
  created_at: string;
  updated_at: string;
}

export interface PqMatchConfirmarRequest {
  acao: AcaoMatch;
  servico_match_id?: string;
  servico_match_tipo?: TipoServicoMatch;
  quantidade?: string;
}
```

- [ ] **Step 2: Adicionar métodos ao objeto proposalsApi**

Após `executeMatch` (linha 101), adicionar:

```typescript
  async listPqItens(propostaId: string, statusMatch?: StatusMatch): Promise<PqItemResponse[]> {
    const params = statusMatch ? { status_match: statusMatch } : undefined;
    const response = await apiClient.get<PqItemResponse[]>(
      `/propostas/${propostaId}/pq/itens`,
      { params },
    );
    return response.data;
  },

  async confirmarMatch(
    propostaId: string,
    itemId: string,
    payload: PqMatchConfirmarRequest,
  ): Promise<PqItemResponse> {
    const response = await apiClient.patch<PqItemResponse>(
      `/propostas/${propostaId}/pq/itens/${itemId}/match`,
      payload,
    );
    return response.data;
  },
```

- [ ] **Step 3: Checar TypeScript**

```bash
cd app/frontend && npx tsc --noEmit 2>&1 | head -20
```
Esperado: sem erros relacionados a `proposalsApi.ts`.

- [ ] **Step 4: Commit**

```bash
git add app/frontend/src/shared/services/api/proposalsApi.ts
git commit -m "feat(f2-03): add PqItem types and listPqItens/confirmarMatch to proposalsApi"
```

---

## Task 4: Frontend — ServicoPickerDialog

**Files:**
- Create: `app/frontend/src/features/proposals/components/ServicoPickerDialog.tsx`

Esse diálogo é chamado quando o usuário clica em "Substituir" em um item. Busca serviços usando o `searchApi` existente e retorna o serviço selecionado.

- [ ] **Step 1: Criar o componente**

```tsx
import { useState } from 'react';
import {
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  List,
  ListItemButton,
  ListItemText,
  TextField,
  Typography,
} from '@mui/material';
import { useMutation } from '@tanstack/react-query';
import { searchApi } from '../../../shared/services/api/searchApi';
import type { ResultadoBusca } from '../../../shared/types/contracts/busca';
import type { TipoServicoMatch } from '../../../shared/services/api/proposalsApi';

interface ServicoPickerDialogProps {
  open: boolean;
  clienteId: string;
  descricaoOriginal: string;
  onSelect: (servicoId: string, tipo: TipoServicoMatch) => void;
  onClose: () => void;
}

export function ServicoPickerDialog({
  open,
  clienteId,
  descricaoOriginal,
  onSelect,
  onClose,
}: ServicoPickerDialogProps) {
  const [texto, setTexto] = useState(descricaoOriginal);

  const buscaMutation = useMutation({
    mutationFn: () =>
      searchApi.buscar({
        cliente_id: clienteId,
        texto_busca: texto,
        limite_resultados: 10,
        threshold_score: 0.5,
      }),
  });

  function handleSelect(resultado: ResultadoBusca) {
    const tipo: TipoServicoMatch =
      resultado.origem_match === 'PROPRIA_CLIENTE' ? 'ITEM_PROPRIO' : 'BASE_TCPO';
    onSelect(resultado.id_tcpo, tipo);
    onClose();
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Substituir Serviço</DialogTitle>
      <DialogContent>
        <TextField
          fullWidth
          label="Buscar serviço"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          sx={{ mt: 1, mb: 2 }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') buscaMutation.mutate();
          }}
        />
        <Button
          variant="outlined"
          onClick={() => buscaMutation.mutate()}
          disabled={buscaMutation.isPending || !texto.trim()}
        >
          {buscaMutation.isPending ? <CircularProgress size={18} /> : 'Buscar'}
        </Button>

        {buscaMutation.isSuccess && buscaMutation.data.resultados.length === 0 && (
          <Typography sx={{ mt: 2 }} color="text.secondary">
            Nenhum resultado encontrado.
          </Typography>
        )}

        {buscaMutation.isSuccess && buscaMutation.data.resultados.length > 0 && (
          <List sx={{ mt: 1 }}>
            {buscaMutation.data.resultados.map((r) => (
              <ListItemButton key={r.id_tcpo} onClick={() => handleSelect(r)}>
                <ListItemText
                  primary={r.descricao}
                  secondary={`${r.codigo_origem} · ${r.unidade} · Confiança: ${(r.score_confianca * 100).toFixed(0)}%`}
                />
              </ListItemButton>
            ))}
          </List>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancelar</Button>
      </DialogActions>
    </Dialog>
  );
}
```

- [ ] **Step 2: Checar TypeScript**

```bash
cd app/frontend && npx tsc --noEmit 2>&1 | head -20
```
Esperado: sem erros.

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/features/proposals/components/ServicoPickerDialog.tsx
git commit -m "feat(f2-03): add ServicoPickerDialog component"
```

---

## Task 5: Frontend — MatchItemRow

**Files:**
- Create: `app/frontend/src/features/proposals/components/MatchItemRow.tsx`

- [ ] **Step 1: Criar o componente**

```tsx
import { useState } from 'react';
import {
  Box,
  Button,
  Chip,
  Stack,
  TableCell,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined';
import SwapHorizOutlinedIcon from '@mui/icons-material/SwapHorizOutlined';
import type { PqItemResponse } from '../../../shared/services/api/proposalsApi';
import { ServicoPickerDialog } from './ServicoPickerDialog';

interface MatchItemRowProps {
  item: PqItemResponse;
  clienteId: string;
  onConfirmar: (itemId: string) => void;
  onRejeitar: (itemId: string) => void;
  onSubstituir: (itemId: string, servicoId: string, tipo: string) => void;
  isLoading: boolean;
}

const STATUS_LABELS: Record<string, { label: string; color: 'success' | 'warning' | 'error' | 'default' | 'info' }> = {
  SUGERIDO: { label: 'Sugerido', color: 'warning' },
  CONFIRMADO: { label: 'Confirmado', color: 'success' },
  MANUAL: { label: 'Manual', color: 'info' },
  SEM_MATCH: { label: 'Sem Match', color: 'error' },
  PENDENTE: { label: 'Pendente', color: 'default' },
  BUSCANDO: { label: 'Buscando', color: 'default' },
};

export function MatchItemRow({
  item,
  clienteId,
  onConfirmar,
  onRejeitar,
  onSubstituir,
  isLoading,
}: MatchItemRowProps) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const status = STATUS_LABELS[item.match_status] ?? { label: item.match_status, color: 'default' };
  const confianca = item.match_confidence
    ? `${(parseFloat(item.match_confidence) * 100).toFixed(0)}%`
    : '—';

  const podeAgir = item.match_status === 'SUGERIDO' || item.match_status === 'PENDENTE';

  return (
    <>
      <TableRow hover sx={{ opacity: isLoading ? 0.5 : 1 }}>
        <TableCell sx={{ width: 50 }}>
          <Typography variant="caption" color="text.secondary">
            {item.linha_planilha ?? '—'}
          </Typography>
        </TableCell>
        <TableCell sx={{ maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          <Tooltip title={item.codigo_original ?? ''}>
            <span>{item.codigo_original ?? '—'}</span>
          </Tooltip>
        </TableCell>
        <TableCell sx={{ maxWidth: 260 }}>
          <Tooltip title={item.descricao_original}>
            <Typography variant="body2" noWrap>{item.descricao_original}</Typography>
          </Tooltip>
        </TableCell>
        <TableCell sx={{ width: 60 }}>
          <Typography variant="body2">{item.unidade_medida_original ?? '—'}</Typography>
        </TableCell>
        <TableCell sx={{ width: 80 }}>
          <Typography variant="body2">{item.quantidade_original ?? '—'}</Typography>
        </TableCell>
        <TableCell sx={{ width: 80 }}>
          <Typography variant="body2" color={parseFloat(item.match_confidence ?? '0') >= 0.8 ? 'success.main' : 'warning.main'}>
            {confianca}
          </Typography>
        </TableCell>
        <TableCell sx={{ width: 120 }}>
          <Chip label={status.label} color={status.color} size="small" />
        </TableCell>
        <TableCell sx={{ width: 220 }}>
          {podeAgir && (
            <Stack direction="row" spacing={0.5}>
              <Tooltip title="Confirmar sugestão">
                <span>
                  <Button
                    size="small"
                    color="success"
                    onClick={() => onConfirmar(item.id)}
                    disabled={isLoading}
                    sx={{ minWidth: 0, px: 1 }}
                  >
                    <CheckCircleOutlineIcon fontSize="small" />
                  </Button>
                </span>
              </Tooltip>
              <Tooltip title="Substituir por outro serviço">
                <span>
                  <Button
                    size="small"
                    color="info"
                    onClick={() => setPickerOpen(true)}
                    disabled={isLoading}
                    sx={{ minWidth: 0, px: 1 }}
                  >
                    <SwapHorizOutlinedIcon fontSize="small" />
                  </Button>
                </span>
              </Tooltip>
              <Tooltip title="Rejeitar (sem match)">
                <span>
                  <Button
                    size="small"
                    color="error"
                    onClick={() => onRejeitar(item.id)}
                    disabled={isLoading}
                    sx={{ minWidth: 0, px: 1 }}
                  >
                    <CancelOutlinedIcon fontSize="small" />
                  </Button>
                </span>
              </Tooltip>
            </Stack>
          )}
        </TableCell>
      </TableRow>

      <ServicoPickerDialog
        open={pickerOpen}
        clienteId={clienteId}
        descricaoOriginal={item.descricao_original}
        onSelect={(servicoId, tipo) => onSubstituir(item.id, servicoId, tipo)}
        onClose={() => setPickerOpen(false)}
      />
    </>
  );
}
```

- [ ] **Step 2: Checar TypeScript**

```bash
cd app/frontend && npx tsc --noEmit 2>&1 | head -20
```
Esperado: sem erros.

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/features/proposals/components/MatchItemRow.tsx
git commit -m "feat(f2-03): add MatchItemRow component with confirm/reject/substitute actions"
```

---

## Task 6: Frontend — MatchReviewPage

**Files:**
- Create: `app/frontend/src/features/proposals/pages/MatchReviewPage.tsx`
- Modify: `app/frontend/src/features/proposals/routes.tsx`

- [ ] **Step 1: Criar a página**

```tsx
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  LinearProgress,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import ArrowBackOutlinedIcon from '@mui/icons-material/ArrowBackOutlined';
import ChecklistOutlinedIcon from '@mui/icons-material/ChecklistOutlined';

import { PageHeader } from '../../../shared/components/PageHeader';
import { proposalsApi } from '../../../shared/services/api/proposalsApi';
import type { TipoServicoMatch } from '../../../shared/services/api/proposalsApi';
import { extractApiErrorMessage } from '../../../shared/services/api/apiClient';
import { MatchItemRow } from '../components/MatchItemRow';

export function MatchReviewPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: proposta } = useQuery({
    queryKey: ['proposta', id],
    queryFn: () => proposalsApi.getById(id!),
    enabled: Boolean(id),
  });

  const { data: itens = [], isLoading, isError, error } = useQuery({
    queryKey: ['pq-itens', id],
    queryFn: () => proposalsApi.listPqItens(id!),
    enabled: Boolean(id),
  });

  const confirmarMutation = useMutation({
    mutationFn: (itemId: string) =>
      proposalsApi.confirmarMatch(id!, itemId, { acao: 'confirmar' }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['pq-itens', id] }),
  });

  const rejeitarMutation = useMutation({
    mutationFn: (itemId: string) =>
      proposalsApi.confirmarMatch(id!, itemId, { acao: 'rejeitar' }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['pq-itens', id] }),
  });

  const substituirMutation = useMutation({
    mutationFn: ({
      itemId,
      servicoId,
      tipo,
    }: {
      itemId: string;
      servicoId: string;
      tipo: TipoServicoMatch;
    }) =>
      proposalsApi.confirmarMatch(id!, itemId, {
        acao: 'substituir',
        servico_match_id: servicoId,
        servico_match_tipo: tipo,
      }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['pq-itens', id] }),
  });

  const confirmados = itens.filter(
    (i) => i.match_status === 'CONFIRMADO' || i.match_status === 'MANUAL',
  ).length;
  const rejeitados = itens.filter((i) => i.match_status === 'SEM_MATCH').length;
  const progresso = itens.length > 0 ? ((confirmados + rejeitados) / itens.length) * 100 : 0;
  const isMutating =
    confirmarMutation.isPending ||
    rejeitarMutation.isPending ||
    substituirMutation.isPending;

  if (isError) return <Alert severity="error">{extractApiErrorMessage(error)}</Alert>;

  return (
    <>
      <PageHeader
        title="Revisão de Match"
        description={`Proposta ${proposta?.codigo ?? ''} — ${itens.length} itens`}
        actions={
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              startIcon={<ArrowBackOutlinedIcon />}
              onClick={() => navigate(`/propostas/${id}/importar`)}
            >
              Voltar
            </Button>
            <Button
              variant="contained"
              startIcon={<ChecklistOutlinedIcon />}
              disabled={confirmados + rejeitados === 0}
              onClick={() => navigate(`/propostas/${id}/cpu`)}
            >
              Ir para CPU ({confirmados} confirmados)
            </Button>
          </Stack>
        }
      />

      <Stack spacing={3}>
        <Paper sx={{ p: 2 }}>
          <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 1 }}>
            <Typography variant="body2">
              Revisados: <strong>{confirmados + rejeitados}</strong> de{' '}
              <strong>{itens.length}</strong>
            </Typography>
            <Typography variant="body2" color="success.main">
              ✓ {confirmados} confirmados
            </Typography>
            <Typography variant="body2" color="error.main">
              ✗ {rejeitados} rejeitados
            </Typography>
          </Stack>
          <LinearProgress variant="determinate" value={progresso} sx={{ height: 8, borderRadius: 4 }} />
        </Paper>

        {(confirmarMutation.isError || rejeitarMutation.isError || substituirMutation.isError) && (
          <Alert severity="error">
            {extractApiErrorMessage(
              confirmarMutation.error ?? rejeitarMutation.error ?? substituirMutation.error,
            )}
          </Alert>
        )}

        <Paper>
          {isLoading ? (
            <Box sx={{ p: 3 }}>
              <LinearProgress />
            </Box>
          ) : (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Linha</TableCell>
                  <TableCell>Código</TableCell>
                  <TableCell>Descrição Original</TableCell>
                  <TableCell>Unid.</TableCell>
                  <TableCell>Qtd</TableCell>
                  <TableCell>Conf.</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Ações</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {itens.map((item) => (
                  <MatchItemRow
                    key={item.id}
                    item={item}
                    clienteId={proposta?.cliente_id ?? ''}
                    isLoading={isMutating}
                    onConfirmar={(itemId) => confirmarMutation.mutate(itemId)}
                    onRejeitar={(itemId) => rejeitarMutation.mutate(itemId)}
                    onSubstituir={(itemId, servicoId, tipo) =>
                      substituirMutation.mutate({
                        itemId,
                        servicoId,
                        tipo: tipo as TipoServicoMatch,
                      })
                    }
                  />
                ))}
                {itens.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                      <Typography color="text.secondary">
                        Nenhum item importado. Execute a importação primeiro.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </Paper>
      </Stack>
    </>
  );
}
```

- [ ] **Step 2: Registrar a rota**

Em `app/frontend/src/features/proposals/routes.tsx`, adicionar lazy import e rota:

```tsx
const MatchReviewPage = lazy(() =>
  import('./pages/MatchReviewPage').then((m) => ({ default: m.MatchReviewPage })),
);
```

E dentro de `<Route path="propostas">`, adicionar:
```tsx
<Route path=":id/match-review" element={<MatchReviewPage />} />
```

O arquivo completo ficará:

```tsx
import { lazy } from 'react';
import { Route } from 'react-router-dom';

const ProposalsListPage = lazy(() =>
  import('./pages/ProposalsListPage').then((m) => ({ default: m.ProposalsListPage })),
);
const ProposalCreatePage = lazy(() =>
  import('./pages/ProposalCreatePage').then((m) => ({ default: m.ProposalCreatePage })),
);
const ProposalDetailPage = lazy(() =>
  import('./pages/ProposalDetailPage').then((m) => ({ default: m.ProposalDetailPage })),
);
const ProposalImportPage = lazy(() =>
  import('./pages/ProposalImportPage').then((m) => ({ default: m.ProposalImportPage })),
);
const ProposalCpuPage = lazy(() =>
  import('./pages/ProposalCpuPage').then((m) => ({ default: m.ProposalCpuPage })),
);
const MatchReviewPage = lazy(() =>
  import('./pages/MatchReviewPage').then((m) => ({ default: m.MatchReviewPage })),
);

export const proposalRoutes = (
  <Route path="propostas">
    <Route index element={<ProposalsListPage />} />
    <Route path="nova" element={<ProposalCreatePage />} />
    <Route path=":id" element={<ProposalDetailPage />} />
    <Route path=":id/importar" element={<ProposalImportPage />} />
    <Route path=":id/match-review" element={<MatchReviewPage />} />
    <Route path=":id/cpu" element={<ProposalCpuPage />} />
  </Route>
);
```

- [ ] **Step 3: Checar TypeScript**

```bash
cd app/frontend && npx tsc --noEmit 2>&1 | head -30
```
Esperado: sem erros em arquivos novos.

- [ ] **Step 4: Commit**

```bash
git add app/frontend/src/features/proposals/pages/MatchReviewPage.tsx app/frontend/src/features/proposals/routes.tsx
git commit -m "feat(f2-03): add MatchReviewPage with progress bar and item table"
```

---

## Task 7: Frontend — botões de acesso nas páginas existentes

**Files:**
- Modify: `app/frontend/src/features/proposals/pages/ProposalImportPage.tsx`
- Modify: `app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx`

- [ ] **Step 1: Atualizar ProposalImportPage**

Após o bloco `{matchMutation.isSuccess && ...}` (linha 147 aprox.), adicionar botão de redirecionamento:

Trocar o bloco de success do match:
```tsx
{matchMutation.isSuccess && (
  <Stack spacing={1} sx={{ mt: 2 }}>
    <Alert severity="info">
      Match concluído: {matchMutation.data.sugeridos} sugestões encontradas,{' '}
      {matchMutation.data.sem_match} itens sem correspondência.
    </Alert>
    <Button
      variant="contained"
      color="secondary"
      onClick={() => navigate(`/propostas/${id}/match-review`)}
    >
      Revisar e Confirmar Match ({matchMutation.data.sugeridos} sugestões)
    </Button>
  </Stack>
)}
```

Adicionar import de `Stack` se não estiver (já está) e garantir que `navigate` está importado (já está).

- [ ] **Step 2: Atualizar ProposalDetailPage**

No bloco de `actions` do `PageHeader` (linha 33 aprox.), adicionar botão "Revisar Match":

```tsx
actions={
  <Stack direction="row" spacing={1}>
    <Button
      variant="outlined"
      startIcon={<FileUploadOutlinedIcon />}
      onClick={() => navigate(`/propostas/${id}/importar`)}
    >
      Importar PQ
    </Button>
    <Button
      variant="outlined"
      color="secondary"
      startIcon={<RuleOutlinedIcon />}
      onClick={() => navigate(`/propostas/${id}/match-review`)}
      disabled={proposta.status === 'RASCUNHO'}
    >
      Revisar Match
    </Button>
    <Button
      variant="contained"
      startIcon={<TableChartOutlinedIcon />}
      onClick={() => navigate(`/propostas/${id}/cpu`)}
      disabled={proposta.status === 'RASCUNHO'}
    >
      Ver CPU
    </Button>
  </Stack>
}
```

Adicionar o import do novo ícone no topo do arquivo:
```tsx
import RuleOutlinedIcon from '@mui/icons-material/RuleOutlined';
```

- [ ] **Step 3: Checar TypeScript completo**

```bash
cd app/frontend && npx tsc --noEmit 2>&1 | head -30
```
Esperado: 0 erros.

- [ ] **Step 4: Rodar suite backend final**

```bash
cd app && python -m pytest backend/tests/ -v --tb=short 2>&1 | tail -5
```
Esperado: 110+ passed, 0 failed.

- [ ] **Step 5: Commit final**

```bash
git add app/frontend/src/features/proposals/pages/ProposalImportPage.tsx app/frontend/src/features/proposals/pages/ProposalDetailPage.tsx
git commit -m "feat(f2-03): wire match-review navigation into ImportPage and DetailPage"
```

---

## Self-Review

**Spec coverage:**
- ✅ Match manual com revisão por item — `MatchReviewPage` + `MatchItemRow`
- ✅ Ver múltiplas opções de substituição — `ServicoPickerDialog` (busca live)
- ✅ Confirmar / Substituir / Rejeitar — 3 ações no `atualizar_match_item` endpoint
- ✅ Progresso visual — `LinearProgress` com contador de confirmados/rejeitados
- ✅ Acesso a partir da `ProposalDetailPage` e `ProposalImportPage`
- ✅ Persistência de histórico implícita: `match_status=CONFIRMADO/MANUAL/SEM_MATCH` + `match_confidence` registrados

**Gaps identificados:** nenhum bloqueante. `quantidade` editável no PATCH mas não exposta na UI desta sprint — pode ser adicionada em F2-06 (edição de PQ).

**Placeholder scan:** sem "TBD", sem "implement later". Todos os steps têm código.

**Type consistency:** `PqMatchConfirmarRequest` usado consistentemente em backend (schema) e frontend (interface). `TipoServicoMatch` definido em `proposalsApi.ts` e re-exportado em `ServicoPickerDialog` e `MatchReviewPage`.
