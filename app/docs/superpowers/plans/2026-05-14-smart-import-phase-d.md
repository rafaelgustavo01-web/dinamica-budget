# Smart Import Engine — Phase D: Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the Smart Import commit to create real `PqImportacao` + `PqItem` records in the existing proposal flow, add a "Importação Inteligente" entry point to `ProposalImportPage`, and verify no dead spike code remains.

**Architecture:** `SmartImportService.commit_job()` gains a private `_write_pq_items()` method that runs inside the existing `db.commit()` transaction — when `job.proposta_id` is set it creates a `PqImportacao` and one `PqItem` per `ITEM` row, matching the exact schema already used by `pq_import_service.py`. The frontend gets one new button on `ProposalImportPage` that opens the Smart Import upload page pre-filled with the proposal's `clienteId`/`propostaId`, and the staging page gains a "Ir para Match" navigation link shown after successful commit.

**Tech Stack:** FastAPI + SQLAlchemy async + PostgreSQL (`operacional` schema). Frontend: React 19 + MUI 7 + React Router 7.

---

## File Map

| Path | Action | Responsibility |
|------|--------|----------------|
| `app/backend/services/smart_import_service.py` | Modify | Add `_write_pq_items()` called at end of `commit_job()` |
| `app/backend/tests/unit/smart_import/test_commit.py` | Modify | Add two tests: PqItem creation path and no-proposta-id path |
| `app/frontend/src/features/smart-import/SmartImportStagingPage.tsx` | Modify | Show "Ir para Match" button after commit when `job.proposta_id` is set |
| `app/frontend/src/features/proposals/pages/ProposalImportPage.tsx` | Modify | Add "Importação Inteligente" alternative in step 1 |

---

## Context you must know before touching any file

### PqItem / PqImportacao schemas (`app/backend/models/proposta.py`)

```python
class PqImportacao(Base, TimestampMixin):
    __tablename__ = "pq_importacoes"
    __table_args__ = {"schema": "operacional"}
    id: UUID (pk, default uuid4)
    proposta_id: UUID (FK propostas, NOT NULL)
    nome_arquivo: str (max 260)
    formato: str (max 10)            # "xlsx" or "csv"
    linhas_total: int
    linhas_importadas: int
    linhas_com_erro: int
    linhas_ignoradas: int
    status: StatusImportacao          # CONCLUIDO | PROCESSANDO | COM_ERROS

class PqItem(Base, TimestampMixin):
    __tablename__ = "pq_itens"
    __table_args__ = {"schema": "operacional"}
    id: UUID (pk, default uuid4)
    proposta_id: UUID (FK propostas, NOT NULL)
    pq_importacao_id: UUID | None (FK pq_importacoes, nullable)
    codigo_original: str | None
    descricao_original: str (NOT NULL)
    unidade_medida_original: str | None
    quantidade_original: Decimal | None
    descricao_tokens: str | None     # normalize_text(descricao) result
    match_status: StatusMatch         # always PENDENTE on creation
    linha_planilha: int | None       # sheet_row from staging
```

### Enums needed

```python
# backend/models/enums.py
class StatusImportacao(str, enum.Enum):
    PROCESSANDO = "PROCESSANDO"
    CONCLUIDO = "CONCLUIDO"
    COM_ERROS = "COM_ERROS"

class StatusMatch(str, enum.Enum):
    PENDENTE = "PENDENTE"
    # ...others not needed here
```

### `normalize_text` for token generation

```python
from backend.repositories.associacao_repository import normalize_text
# normalize_text(descricao: str) -> str — synchronous, no DB calls
```

### SmartImportJob payload structure (already in DB after staging)

`job.payload_staging["rows"]` is a list of dicts:
```python
{
  "idx": int,
  "sheet_row": int | None,
  "row_class": "ITEM" | "SECAO" | "TOTAL" | "VAZIA",
  "codigo": str | None,
  "descricao": str | None,
  "unidade": str | None,
  "quantidade": str | None,   # stored as string — must parse to Decimal
  "preco": str | None,
  "valor": str | None,
}
```

Only rows where `row_class == "ITEM"` and `descricao` is non-empty become `PqItem` records.

---

## Task D1: `_write_pq_items` — backend transactional write

**Files:**
- Modify: `app/backend/services/smart_import_service.py`

The method runs **before** the final `await db.commit()` in `commit_job()`, so it participates in the same transaction. If anything fails, the whole commit rolls back.

- [ ] **Step 1: Write the two failing tests**

Open `app/backend/tests/unit/smart_import/test_commit.py` and add at the bottom:

```python
@pytest.mark.asyncio
async def test_commit_job_with_proposta_id_creates_pq_items(db):
    """When proposta_id is set, commit_job should db.add a PqImportacao and PqItems."""
    from backend.models.proposta import PqImportacao, PqItem as PqItemModel

    mock_profile = _mock_profile()
    mock_repo = AsyncMock()
    mock_repo.get_by_cliente_id.return_value = mock_profile
    mock_repo.save_corrections.return_value = []

    proposta_id = uuid4()
    job = MagicMock()
    job.id = uuid4()
    job.cliente_id = uuid4()
    job.proposta_id = proposta_id
    job.arquivo_origem = "planilha.xlsx"
    job.status = SmartImportStatus.REVIEW_REQUIRED
    job.profile_id = None
    job.payload_staging = {
        "rows": [
            {
                "idx": 0, "sheet_row": 2, "row_class": "ITEM",
                "codigo": "1.1", "descricao": "Escavacao manual",
                "unidade": "m2", "quantidade": "10", "preco": None, "valor": None,
            },
            {
                "idx": 1, "sheet_row": 3, "row_class": "SECAO",
                "codigo": None, "descricao": "SERVICOS PRELIMINARES",
                "unidade": None, "quantidade": None, "preco": None, "valor": None,
            },
        ]
    }

    added_objects = []
    db.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))
    db.flush = AsyncMock()

    with patch("backend.services.smart_import_service.ImportProfileRepository") as mock_cls:
        mock_cls.return_value = mock_repo
        await SmartImportService().commit_job(job, db, corrections=[])

    importacoes = [o for o in added_objects if isinstance(o, PqImportacao)]
    pq_items = [o for o in added_objects if isinstance(o, PqItemModel)]

    assert len(importacoes) == 1
    assert importacoes[0].proposta_id == proposta_id
    assert importacoes[0].nome_arquivo == "planilha.xlsx"
    assert importacoes[0].linhas_importadas == 1
    assert importacoes[0].linhas_ignoradas == 1

    assert len(pq_items) == 1
    assert pq_items[0].proposta_id == proposta_id
    assert pq_items[0].descricao_original == "Escavacao manual"
    assert pq_items[0].codigo_original == "1.1"
    assert pq_items[0].unidade_medida_original == "m2"
    assert pq_items[0].linha_planilha == 2


@pytest.mark.asyncio
async def test_commit_job_without_proposta_id_skips_pq_items(db):
    """When proposta_id is None, no PqImportacao or PqItem is created."""
    from backend.models.proposta import PqImportacao, PqItem as PqItemModel

    mock_profile = _mock_profile()
    mock_repo = AsyncMock()
    mock_repo.get_by_cliente_id.return_value = mock_profile
    mock_repo.save_corrections.return_value = []

    job = MagicMock()
    job.id = uuid4()
    job.cliente_id = uuid4()
    job.proposta_id = None
    job.arquivo_origem = "planilha.xlsx"
    job.status = SmartImportStatus.REVIEW_REQUIRED
    job.profile_id = None
    job.payload_staging = {
        "rows": [
            {
                "idx": 0, "sheet_row": 2, "row_class": "ITEM",
                "codigo": "1.1", "descricao": "Escavacao",
                "unidade": "m2", "quantidade": "5", "preco": None, "valor": None,
            },
        ]
    }

    added_objects = []
    db.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))

    with patch("backend.services.smart_import_service.ImportProfileRepository") as mock_cls:
        mock_cls.return_value = mock_repo
        await SmartImportService().commit_job(job, db, corrections=[])

    assert not any(isinstance(o, PqImportacao) for o in added_objects)
    assert not any(isinstance(o, PqItemModel) for o in added_objects)
```

- [ ] **Step 2: Run the tests — verify they FAIL**

```bash
cd app && python -m pytest backend/tests/unit/smart_import/test_commit.py::test_commit_job_with_proposta_id_creates_pq_items backend/tests/unit/smart_import/test_commit.py::test_commit_job_without_proposta_id_skips_pq_items -v --tb=short
```

Expected: both FAIL (`_write_pq_items` does not exist yet).

- [ ] **Step 3: Implement `_write_pq_items` in `smart_import_service.py`**

Add the following imports at the top of `app/backend/services/smart_import_service.py` (after existing imports):

```python
from backend.models.enums import StatusImportacao, StatusMatch
from backend.models.proposta import PqImportacao, PqItem
from backend.repositories.associacao_repository import normalize_text
```

Add `_write_pq_items` as a new method of `SmartImportService`, **before** `commit_job`:

```python
async def _write_pq_items(self, job: SmartImportJob, db: AsyncSession) -> None:
    from decimal import Decimal, InvalidOperation

    rows = (job.payload_staging or {}).get("rows", [])
    item_rows = [r for r in rows if r.get("row_class") == "ITEM" and r.get("descricao")]
    non_item_count = len(rows) - len(item_rows)
    ext = job.arquivo_origem.rsplit(".", 1)[-1].lower() if "." in job.arquivo_origem else "xlsx"

    importacao = PqImportacao(
        proposta_id=job.proposta_id,
        nome_arquivo=job.arquivo_origem,
        formato=ext,
        linhas_total=len(rows),
        linhas_importadas=len(item_rows),
        linhas_com_erro=0,
        linhas_ignoradas=non_item_count,
        status=StatusImportacao.CONCLUIDO,
    )
    db.add(importacao)
    await db.flush()

    for row in item_rows:
        descricao = str(row["descricao"]).strip()
        qtd_raw = row.get("quantidade")
        try:
            quantidade = Decimal(str(qtd_raw).strip().replace(",", ".")) if qtd_raw else None
        except InvalidOperation:
            quantidade = None

        pq_item = PqItem(
            proposta_id=job.proposta_id,
            pq_importacao_id=importacao.id,
            codigo_original=row.get("codigo"),
            descricao_original=descricao,
            unidade_medida_original=row.get("unidade"),
            quantidade_original=quantidade,
            descricao_tokens=normalize_text(descricao),
            match_status=StatusMatch.PENDENTE,
            linha_planilha=row.get("sheet_row"),
        )
        db.add(pq_item)
```

Then, in `commit_job`, add the call to `_write_pq_items` **after** the profile update lines and **before** `await db.commit()`. The full tail of `commit_job` should look like:

```python
        profile.header_row_strategy = updated["header_row_strategy"]
        profile.column_aliases = updated["column_aliases"]
        profile.aba_pattern = updated.get("aba_pattern")
        profile.uso_count = updated["uso_count"]
        profile.score_confianca = Decimal(str(updated["score_confianca"]))

        job.profile_id = profile.id
        job.status = SmartImportStatus.COMPLETED

        if job.proposta_id:
            await self._write_pq_items(job, db)

        await db.commit()
        logger.info(f"SmartImportJob {job.id} committed. Profile {profile.id} score={profile.score_confianca}")
        return job
```

- [ ] **Step 4: Run the tests — verify they PASS**

```bash
cd app && python -m pytest backend/tests/unit/smart_import/test_commit.py -v --tb=short
```

Expected: all 6 tests in the file pass (4 existing + 2 new).

- [ ] **Step 5: Run full smart_import suite**

```bash
cd app && python -m pytest backend/tests/unit/smart_import/ -v --tb=short 2>&1 | tail -15
```

Expected: `47 passed`.

- [ ] **Step 6: Commit**

```bash
git add app/backend/services/smart_import_service.py app/backend/tests/unit/smart_import/test_commit.py
git commit -m "feat(smart-import/phase-d): commit_job writes PqImportacao + PqItem when proposta_id is set"
```

---

## Task D2: Frontend — "Ir para Match" on staging page after commit

**Files:**
- Modify: `app/frontend/src/features/smart-import/SmartImportStagingPage.tsx`

After a successful commit where `job.proposta_id` is set, show a "Ir para Match Inteligente" button that navigates back to `/propostas/:propostaId/importar` — where `hasPqItems` will now be `true` and the user can run the match.

- [ ] **Step 1: Add navigate import and button to the success alert section**

In `SmartImportStagingPage.tsx`, the `useNavigate` hook is already imported from `react-router-dom`. Add the button inside the success `Alert` block.

Find this block:

```tsx
        {commitMutation.isSuccess && (
          <Alert severity="success" icon={<CheckCircleOutlineIcon />}>
            Importação commitada. Perfil atualizado — confiança:{' '}
            <strong>{(commitMutation.data.score_confianca * 100).toFixed(1)}%</strong> ·{' '}
            {commitMutation.data.corrections_applied} correção(ões) aplicada(s).
          </Alert>
        )}
```

Replace with:

```tsx
        {commitMutation.isSuccess && (
          <Alert
            severity="success"
            icon={<CheckCircleOutlineIcon />}
            action={
              job.proposta_id ? (
                <Button
                  color="inherit"
                  size="small"
                  onClick={() => navigate(`/propostas/${job.proposta_id}/importar`)}
                >
                  Ir para Match
                </Button>
              ) : undefined
            }
          >
            Importação commitada. Perfil atualizado — confiança:{' '}
            <strong>{(commitMutation.data.score_confianca * 100).toFixed(1)}%</strong> ·{' '}
            {commitMutation.data.corrections_applied} correção(ões) aplicada(s).
          </Alert>
        )}
```

- [ ] **Step 2: Add `useNavigate` — it is already imported, verify it is wired**

Check that `useNavigate` is in the imports at the top of `SmartImportStagingPage.tsx`:

```tsx
import { useParams, useNavigate } from 'react-router-dom';
```

And that `navigate` is declared inside the component:

```tsx
const navigate = useNavigate();
```

Both already exist from Phase C. No change needed.

- [ ] **Step 3: Type-check**

```bash
cd app/frontend && npx tsc --noEmit 2>&1 | grep -i "SmartImportStaging" | head -10
```

Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add app/frontend/src/features/smart-import/SmartImportStagingPage.tsx
git commit -m "feat(smart-import/phase-d): show 'Ir para Match' button after commit when linked to proposal"
```

---

## Task D3: Frontend — "Importação Inteligente" button on ProposalImportPage

**Files:**
- Modify: `app/frontend/src/features/proposals/pages/ProposalImportPage.tsx`

Add a secondary path in Step 1 that opens the Smart Import upload page pre-filled with `clienteId` and `propostaId`. The existing "Enviar Planilha" flow is untouched — Smart Import is an **alternative**, not a replacement.

- [ ] **Step 1: Add the Smart Import button to Step 1 paper**

The current Step 1 block ends at the success `Alert`. Add a `Divider` + alternative button **after** the success alert and **before** the closing `</Paper>` tag.

Find the end of the Step 1 `<Paper>`:

```tsx
          {uploadMutation.isSuccess && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Planilha importada com sucesso: {uploadMutation.data.linhas_importadas} linhas processadas
              {uploadMutation.data.linhas_ignoradas > 0 && (
                <>, {uploadMutation.data.linhas_ignoradas} título(s)/seção(oes) ignorados</>
              )}
              {uploadMutation.data.linhas_com_erro > 0 && (
                <>, {uploadMutation.data.linhas_com_erro} com erro</>
              )}
              .
            </Alert>
          )}
        </Paper>
```

Replace with:

```tsx
          {uploadMutation.isSuccess && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Planilha importada com sucesso: {uploadMutation.data.linhas_importadas} linhas processadas
              {uploadMutation.data.linhas_ignoradas > 0 && (
                <>, {uploadMutation.data.linhas_ignoradas} título(s)/seção(oes) ignorados</>
              )}
              {uploadMutation.data.linhas_com_erro > 0 && (
                <>, {uploadMutation.data.linhas_com_erro} com erro</>
              )}
              .
            </Alert>
          )}

          <Divider sx={{ my: 2 }}>ou</Divider>

          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Prefere revisar linha a linha antes de importar?
          </Typography>
          <Button
            variant="outlined"
            color="secondary"
            onClick={() =>
              navigate(
                `/smart-import/upload?clienteId=${proposta.cliente_id}&propostaId=${id}`,
              )
            }
          >
            Importação Inteligente (Smart Import)
          </Button>
        </Paper>
```

- [ ] **Step 2: Add `Divider` to the MUI import line**

Find the existing MUI import in `ProposalImportPage.tsx`:

```tsx
import { Paper, Stack, Typography, Button, Alert, Box, CircularProgress, LinearProgress } from '@mui/material';
```

Replace with:

```tsx
import { Paper, Stack, Typography, Button, Alert, Box, CircularProgress, Divider, LinearProgress } from '@mui/material';
```

- [ ] **Step 3: Type-check**

```bash
cd app/frontend && npx tsc --noEmit 2>&1 | grep -i "ProposalImport" | head -10
```

Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add app/frontend/src/features/proposals/pages/ProposalImportPage.tsx
git commit -m "feat(smart-import/phase-d): add 'Importação Inteligente' alternative in ProposalImportPage step 1"
```

---

## Task D4: Cleanup — verify no dead spike code remains

**Files:**
- Verify: `app/backend/services/smart_import_service.py`

The original spike used hardcoded rows and mock responses before the real pipeline (FileExtractor → HeaderDetector → ColumnMapper → RowClassifier) was built. This task confirms the service is clean and removes any remnants found.

- [ ] **Step 1: Scan for dead code markers**

```bash
grep -n "TODO\|FIXME\|HACK\|mock\|hardcoded\|placeholder\|fake\|dummy\|spike" \
  app/backend/services/smart_import_service.py
```

Expected: no output. If any lines appear, read them and remove the dead code before proceeding.

- [ ] **Step 2: Confirm all pipeline components are imported and used**

```bash
grep -n "FileExtractor\|HeaderDetector\|ColumnMapper\|RowClassifier\|ProfileLearner" \
  app/backend/services/smart_import_service.py
```

Expected: at least one match per component (they are all used in `create_job` and `commit_job`). If any are imported but not used, remove the unused import.

- [ ] **Step 3: Run full backend test suite for smart_import**

```bash
cd app && python -m pytest backend/tests/unit/smart_import/ -v 2>&1 | tail -5
```

Expected: `47 passed, 0 failed`.

- [ ] **Step 4: Commit (only if files changed in steps 1–2)**

If no dead code was found (likely), skip this commit. If files were changed:

```bash
git add app/backend/services/smart_import_service.py
git commit -m "chore(smart-import): remove dead spike code from smart_import_service"
```

---

## Self-Review

### Spec Coverage

| Requirement | Task |
|------------|------|
| Wiring com PqItem (commit transacional) | D1 — `_write_pq_items` + `PqImportacao` created in same transaction as profile update |
| Migração do fluxo atual: botão Smart Import ao lado do import existente | D3 — `Divider` + "Importação Inteligente" button in `ProposalImportPage` step 1 |
| Cleanup do spike morto | D4 — grep + verification |
| User can navigate back to proposal match after smart import commit | D2 — "Ir para Match" button in staging success alert |

All 4 requirements covered. ✓

### Placeholder Scan

No TBD/TODO/placeholder patterns. All code blocks are complete and reference types defined in the Context section above.

### Type Consistency

- `PqImportacao` and `PqItem` — field names match the schema documented in the Context section and used verbatim in `_write_pq_items`
- `StatusImportacao.CONCLUIDO` / `StatusMatch.PENDENTE` — exact enum values from `backend/models/enums.py`
- `normalize_text(descricao: str) -> str` — synchronous, imported from `associacao_repository`
- Frontend: `job.proposta_id: string | null` — matches `SmartImportJob` interface from `smartImportApi.ts`; guarded with truthiness check before rendering the "Ir para Match" button
