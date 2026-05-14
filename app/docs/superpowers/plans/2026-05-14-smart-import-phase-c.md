# Smart Import Engine — Phase C: Frontend Staging UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the React frontend for the Smart Import Engine: file upload form, staging review table with row edit/add/delete/reclassify, and a commit button that sends corrections to the backend for profile learning.

**Architecture:** Two pages under a new `features/smart-import/` folder. `SmartImportUploadPage` handles file upload (POST multipart to `/api/v1/smart-import`) and navigates to `SmartImportStagingPage` where the user reviews and edits the detected rows before committing. Corrections (reclassify events) are accumulated in local state and sent with the commit call so the backend `ProfileLearner` can improve the client's import profile.

**Tech Stack:** React 19 + TypeScript 5.9 + MUI 7 + TanStack React Query 5 + React Router 7 + Axios (via existing `apiClient`). No new dependencies.

---

## File Map

| Path | Action | Responsibility |
|------|--------|----------------|
| `frontend/src/shared/services/api/smartImportApi.ts` | Create | All HTTP calls for the smart-import feature |
| `frontend/src/features/smart-import/SmartImportUploadPage.tsx` | Create | File picker + client context → upload → redirect |
| `frontend/src/features/smart-import/SmartImportStagingPage.tsx` | Create | Load job, display/edit rows, commit |
| `frontend/src/features/smart-import/RowEditDialog.tsx` | Create | MUI Dialog for editing a single staging row |
| `frontend/src/features/smart-import/routes.tsx` | Create | Lazy imports + Route declarations for this feature |
| `frontend/src/app/router.tsx` | Modify | Register smart-import routes inside `AuthenticatedApp` |

---

## Task C1: API Service

**Files:**
- Create: `app/frontend/src/shared/services/api/smartImportApi.ts`

No tests — API services are thin wrappers validated via TypeScript. Run `tsc --noEmit` to verify.

- [ ] **Step 1: Create the API service file**

```typescript
// app/frontend/src/shared/services/api/smartImportApi.ts
import { apiClient } from './apiClient';

export type RowClass = 'ITEM' | 'SECAO' | 'TOTAL' | 'VAZIA';
export type SmartImportStatus = 'PENDING' | 'REVIEW_REQUIRED' | 'COMPLETED';

export interface StagingRow {
  idx: number;
  sheet_row: number | null;
  row_class: RowClass;
  codigo: string | null;
  descricao: string | null;
  unidade: string | null;
  quantidade: string | null;
  preco: string | null;
  valor: string | null;
}

export interface SmartImportJob {
  id: string;
  cliente_id: string;
  proposta_id: string | null;
  arquivo_origem: string;
  status: SmartImportStatus;
  detected_header_row: number | null;
  detected_data_range: Record<string, unknown> | null;
  mapping_metadata: Record<string, unknown> | null;
  rows: StagingRow[];
}

export interface CommitJobResponse {
  job_id: string;
  status: SmartImportStatus;
  profile_id: string;
  score_confianca: number;
  uso_count: number;
  corrections_applied: number;
}

export interface CorrectionEntry {
  tipo: 'COLUMN_REMAP' | 'HEADER_ROW_FIX' | 'ROW_RECLASSIFY' | 'SHEET_CHANGE';
  detalhe: Record<string, unknown>;
}

export type RowPatch = Partial<Pick<StagingRow, 'codigo' | 'descricao' | 'unidade' | 'quantidade' | 'preco' | 'valor'>>;

export const smartImportApi = {
  upload: (params: {
    file: File;
    cliente_id: string;
    proposta_id?: string;
  }): Promise<SmartImportJob> => {
    const fd = new FormData();
    fd.append('file', params.file);
    fd.append('cliente_id', params.cliente_id);
    if (params.proposta_id) fd.append('proposta_id', params.proposta_id);
    return apiClient.post<SmartImportJob>('/smart-import', fd).then((r) => r.data);
  },

  getJob: (jobId: string): Promise<SmartImportJob> =>
    apiClient.get<SmartImportJob>(`/smart-import/${jobId}`).then((r) => r.data),

  editRow: (jobId: string, rowIdx: number, patch: RowPatch): Promise<StagingRow> =>
    apiClient
      .patch<StagingRow>(`/smart-import/${jobId}/rows/${rowIdx}`, patch)
      .then((r) => r.data),

  addRow: (
    jobId: string,
    data: Omit<StagingRow, 'idx' | 'sheet_row' | 'row_class'> & { descricao: string },
  ): Promise<StagingRow> =>
    apiClient.post<StagingRow>(`/smart-import/${jobId}/rows`, data).then((r) => r.data),

  deleteRow: (jobId: string, rowIdx: number): Promise<void> =>
    apiClient.delete(`/smart-import/${jobId}/rows/${rowIdx}`).then(() => undefined),

  classifyRow: (jobId: string, rowIdx: number, row_class: RowClass): Promise<StagingRow> =>
    apiClient
      .patch<StagingRow>(`/smart-import/${jobId}/rows/${rowIdx}/classify`, { row_class })
      .then((r) => r.data),

  commitJob: (jobId: string, corrections: CorrectionEntry[]): Promise<CommitJobResponse> =>
    apiClient
      .post<CommitJobResponse>(`/smart-import/${jobId}/commit`, { corrections })
      .then((r) => r.data),
};
```

- [ ] **Step 2: Type-check**

```bash
cd app/frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: no errors related to `smartImportApi.ts`.

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/shared/services/api/smartImportApi.ts
git commit -m "feat(smart-import/phase-c): add smartImportApi service with full type signatures"
```

---

## Task C2: RowEditDialog

**Files:**
- Create: `app/frontend/src/features/smart-import/RowEditDialog.tsx`

- [ ] **Step 1: Create the dialog component**

```tsx
// app/frontend/src/features/smart-import/RowEditDialog.tsx
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
} from '@mui/material';
import { useEffect, useState } from 'react';

import type { StagingRow, RowPatch } from '../../shared/services/api/smartImportApi';

interface Props {
  open: boolean;
  row: StagingRow | null;
  onClose: () => void;
  onSave: (patch: RowPatch) => void;
  loading?: boolean;
}

export function RowEditDialog({ open, row, onClose, onSave, loading = false }: Props) {
  const [fields, setFields] = useState<RowPatch>({});

  useEffect(() => {
    if (row) {
      setFields({
        codigo: row.codigo ?? '',
        descricao: row.descricao ?? '',
        unidade: row.unidade ?? '',
        quantidade: row.quantidade ?? '',
        preco: row.preco ?? '',
        valor: row.valor ?? '',
      });
    }
  }, [row]);

  const set = (key: keyof RowPatch) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setFields((prev) => ({ ...prev, [key]: e.target.value }));

  const handleSave = () => {
    const patch: RowPatch = {};
    for (const [k, v] of Object.entries(fields)) {
      if (v !== undefined) patch[k as keyof RowPatch] = v === '' ? null : v;
    }
    onSave(patch);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Editar Linha</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          <TextField label="Código" value={fields.codigo ?? ''} onChange={set('codigo')} size="small" />
          <TextField
            label="Descrição"
            value={fields.descricao ?? ''}
            onChange={set('descricao')}
            size="small"
            required
          />
          <TextField label="Unidade" value={fields.unidade ?? ''} onChange={set('unidade')} size="small" />
          <TextField label="Quantidade" value={fields.quantidade ?? ''} onChange={set('quantidade')} size="small" />
          <TextField label="Preço" value={fields.preco ?? ''} onChange={set('preco')} size="small" />
          <TextField label="Valor" value={fields.valor ?? ''} onChange={set('valor')} size="small" />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancelar
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={loading || !fields.descricao}
          loading={loading}
        >
          Salvar
        </Button>
      </DialogActions>
    </Dialog>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd app/frontend && npx tsc --noEmit 2>&1 | grep -i "RowEditDialog" | head -10
```

Expected: no output (no errors).

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/features/smart-import/RowEditDialog.tsx
git commit -m "feat(smart-import/phase-c): add RowEditDialog component"
```

---

## Task C3: Upload Page

**Files:**
- Create: `app/frontend/src/features/smart-import/SmartImportUploadPage.tsx`

The page reads `clienteId` and `propostaId` from URL query params (so it can be linked from proposal detail pages with those pre-filled) and falls back to empty strings that the user must fill in.

- [ ] **Step 1: Create the upload page**

```tsx
// app/frontend/src/features/smart-import/SmartImportUploadPage.tsx
import CloudUploadOutlinedIcon from '@mui/icons-material/CloudUploadOutlined';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useMutation } from '@tanstack/react-query';
import { useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { PageHeader } from '../../shared/components/PageHeader';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import { smartImportApi } from '../../shared/services/api/smartImportApi';

export function SmartImportUploadPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const fileRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [clienteId, setClienteId] = useState(searchParams.get('clienteId') ?? '');
  const [propostaId] = useState(searchParams.get('propostaId') ?? '');

  const uploadMutation = useMutation({
    mutationFn: () =>
      smartImportApi.upload({
        file: file!,
        cliente_id: clienteId.trim(),
        proposta_id: propostaId.trim() || undefined,
      }),
    onSuccess: (job) => {
      navigate(`/smart-import/${job.id}`);
    },
  });

  const canSubmit = !!file && clienteId.trim().length > 0 && !uploadMutation.isPending;

  return (
    <>
      <PageHeader
        title="Smart Import"
        description="Carregue uma planilha para importação inteligente"
      />

      <Paper sx={{ p: 3, maxWidth: 560 }}>
        <Stack spacing={3}>
          <TextField
            label="ID do Cliente"
            value={clienteId}
            onChange={(e) => setClienteId(e.target.value)}
            size="small"
            required
            helperText="UUID do cliente para qual esta planilha pertence"
          />

          {propostaId && (
            <TextField
              label="ID da Proposta (pré-preenchido)"
              value={propostaId}
              size="small"
              disabled
            />
          )}

          <Box>
            <input
              ref={fileRef}
              type="file"
              accept=".xlsx,.csv"
              style={{ display: 'none' }}
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            <Stack direction="row" spacing={2} alignItems="center">
              <Button
                variant="outlined"
                startIcon={<CloudUploadOutlinedIcon />}
                onClick={() => fileRef.current?.click()}
              >
                Selecionar Arquivo
              </Button>
              {file && (
                <Typography variant="body2" color="text.secondary">
                  {file.name} ({(file.size / 1024).toFixed(0)} KB)
                </Typography>
              )}
            </Stack>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
              Formatos aceitos: .xlsx, .csv (máx. 10 MB)
            </Typography>
          </Box>

          {uploadMutation.isError && (
            <Alert severity="error">
              {extractApiErrorMessage(uploadMutation.error)}
            </Alert>
          )}

          <Button
            variant="contained"
            disabled={!canSubmit}
            onClick={() => uploadMutation.mutate()}
            loading={uploadMutation.isPending}
          >
            Importar Planilha
          </Button>
        </Stack>
      </Paper>
    </>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd app/frontend && npx tsc --noEmit 2>&1 | grep -i "SmartImportUpload" | head -10
```

Expected: no output.

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/features/smart-import/SmartImportUploadPage.tsx
git commit -m "feat(smart-import/phase-c): add SmartImportUploadPage"
```

---

## Task C4: Staging Page

**Files:**
- Create: `app/frontend/src/features/smart-import/SmartImportStagingPage.tsx`

This is the core page. It:
1. Loads the job via `useQuery`
2. Renders a table of staging rows with class chips
3. Handles edit (opens `RowEditDialog` → `PATCH /rows/:idx`), delete (`DELETE /rows/:idx`), reclassify (menu → `PATCH /rows/:idx/classify`)
4. "Adicionar Linha" button opens the dialog in add mode
5. Accumulates `ROW_RECLASSIFY` corrections in local state
6. "Commitar" button calls `POST /commit` with collected corrections, then shows success

- [ ] **Step 1: Create the staging page**

```tsx
// app/frontend/src/features/smart-import/SmartImportStagingPage.tsx
import AddIcon from '@mui/icons-material/Add';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  IconButton,
  Menu,
  MenuItem,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '../../shared/components/PageHeader';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import {
  type CorrectionEntry,
  type RowClass,
  type RowPatch,
  type StagingRow,
  smartImportApi,
} from '../../shared/services/api/smartImportApi';
import { RowEditDialog } from './RowEditDialog';

const ROW_CLASS_OPTIONS: RowClass[] = ['ITEM', 'SECAO', 'TOTAL', 'VAZIA'];

const CLASS_CHIP_COLOR: Record<RowClass, 'primary' | 'secondary' | 'error' | 'default'> = {
  ITEM: 'primary',
  SECAO: 'secondary',
  TOTAL: 'error',
  VAZIA: 'default',
};

export function SmartImportStagingPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [corrections, setCorrections] = useState<CorrectionEntry[]>([]);
  const [editTarget, setEditTarget] = useState<StagingRow | null>(null);
  const [addMode, setAddMode] = useState(false);

  // Classify menu state
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [menuRow, setMenuRow] = useState<StagingRow | null>(null);

  const { data: job, isLoading, isError, error } = useQuery({
    queryKey: ['smart-import-job', jobId],
    queryFn: () => smartImportApi.getJob(jobId!),
    enabled: Boolean(jobId),
  });

  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: ['smart-import-job', jobId] });

  const editMutation = useMutation({
    mutationFn: ({ rowIdx, patch }: { rowIdx: number; patch: RowPatch }) =>
      smartImportApi.editRow(jobId!, rowIdx, patch),
    onSuccess: () => {
      setEditTarget(null);
      void invalidate();
    },
  });

  const addMutation = useMutation({
    mutationFn: (data: Parameters<typeof smartImportApi.addRow>[1]) =>
      smartImportApi.addRow(jobId!, data),
    onSuccess: () => {
      setAddMode(false);
      void invalidate();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (rowIdx: number) => smartImportApi.deleteRow(jobId!, rowIdx),
    onSuccess: () => void invalidate(),
  });

  const classifyMutation = useMutation({
    mutationFn: ({ rowIdx, row_class }: { rowIdx: number; row_class: RowClass }) =>
      smartImportApi.classifyRow(jobId!, rowIdx, row_class),
    onSuccess: (_, { rowIdx, row_class }) => {
      const original = job?.rows.find((r) => r.idx === rowIdx);
      if (original && original.row_class !== row_class) {
        setCorrections((prev) => [
          ...prev,
          {
            tipo: 'ROW_RECLASSIFY',
            detalhe: {
              descricao: original.descricao ?? '',
              de: original.row_class,
              para: row_class,
            },
          },
        ]);
      }
      setMenuAnchor(null);
      setMenuRow(null);
      void invalidate();
    },
  });

  const commitMutation = useMutation({
    mutationFn: () => smartImportApi.commitJob(jobId!, corrections),
    onSuccess: (result) => {
      void queryClient.invalidateQueries({ queryKey: ['smart-import-job', jobId] });
      void queryClient.invalidateQueries({ queryKey: ['proposta'] });
    },
  });

  const handleSaveEdit = (patch: RowPatch) => {
    if (!editTarget) return;
    editMutation.mutate({ rowIdx: editTarget.idx, patch });
  };

  const handleSaveAdd = (patch: RowPatch) => {
    addMutation.mutate({
      descricao: patch.descricao ?? '',
      codigo: patch.codigo ?? undefined,
      unidade: patch.unidade ?? undefined,
      quantidade: patch.quantidade ?? undefined,
      preco: patch.preco ?? undefined,
      valor: patch.valor ?? undefined,
    });
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError || !job) {
    return (
      <>
        <PageHeader title="Smart Import — Staging" description="Erro ao carregar job" />
        <Alert severity="error">{extractApiErrorMessage(error)}</Alert>
      </>
    );
  }

  const committed = job.status === 'COMPLETED' && commitMutation.isSuccess;

  return (
    <>
      <PageHeader
        title={`Smart Import — ${job.arquivo_origem}`}
        description={`${job.rows.length} linhas detectadas · Linha de cabeçalho: ${job.detected_header_row ?? '—'}`}
      />

      <Stack spacing={2}>
        {/* Status banner */}
        {job.status === 'REVIEW_REQUIRED' && (
          <Alert severity="warning">
            Algumas linhas precisam de revisão. Verifique itens sem quantidade ou descrição.
          </Alert>
        )}

        {commitMutation.isSuccess && (
          <Alert severity="success" icon={<CheckCircleOutlineIcon />}>
            Importação commitada. Perfil atualizado — confiança:{' '}
            <strong>{(commitMutation.data.score_confianca * 100).toFixed(1)}%</strong> ·{' '}
            {commitMutation.data.corrections_applied} correções aplicadas.
          </Alert>
        )}

        {commitMutation.isError && (
          <Alert severity="error">{extractApiErrorMessage(commitMutation.error)}</Alert>
        )}

        {/* Actions bar */}
        <Stack direction="row" spacing={2} justifyContent="space-between" alignItems="center">
          <Button
            startIcon={<AddIcon />}
            variant="outlined"
            onClick={() => setAddMode(true)}
            disabled={committed}
          >
            Adicionar Linha
          </Button>
          <Button
            variant="contained"
            color="success"
            disabled={committed || commitMutation.isPending}
            loading={commitMutation.isPending}
            onClick={() => commitMutation.mutate()}
          >
            Commitar Importação
          </Button>
        </Stack>

        {/* Staging table */}
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell width={100}>Classe</TableCell>
                <TableCell width={80}>Código</TableCell>
                <TableCell>Descrição</TableCell>
                <TableCell width={70}>Unid.</TableCell>
                <TableCell width={80}>Qtd</TableCell>
                <TableCell width={100}>Preço</TableCell>
                <TableCell width={100}>Valor</TableCell>
                <TableCell width={90} align="right">
                  Ações
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {job.rows.map((row) => (
                <TableRow
                  key={row.idx}
                  sx={{
                    opacity: row.row_class === 'VAZIA' ? 0.4 : 1,
                    bgcolor:
                      row.row_class === 'SECAO'
                        ? 'action.hover'
                        : row.row_class === 'TOTAL'
                          ? 'error.light'
                          : 'inherit',
                  }}
                >
                  <TableCell>
                    <Tooltip title="Clique para reclassificar">
                      <Chip
                        label={row.row_class}
                        size="small"
                        color={CLASS_CHIP_COLOR[row.row_class]}
                        onClick={(e) => {
                          setMenuAnchor(e.currentTarget);
                          setMenuRow(row);
                        }}
                        clickable
                      />
                    </Tooltip>
                  </TableCell>
                  <TableCell>{row.codigo ?? '—'}</TableCell>
                  <TableCell>
                    <Typography
                      variant="body2"
                      fontWeight={row.row_class === 'SECAO' ? 600 : 400}
                    >
                      {row.descricao ?? '—'}
                    </Typography>
                  </TableCell>
                  <TableCell>{row.unidade ?? '—'}</TableCell>
                  <TableCell
                    sx={{
                      color:
                        row.row_class === 'ITEM' && !row.quantidade ? 'warning.main' : 'inherit',
                    }}
                  >
                    {row.quantidade ?? (row.row_class === 'ITEM' ? '⚠ —' : '—')}
                  </TableCell>
                  <TableCell>{row.preco ?? '—'}</TableCell>
                  <TableCell>{row.valor ?? '—'}</TableCell>
                  <TableCell align="right">
                    <Tooltip title="Editar">
                      <IconButton
                        size="small"
                        onClick={() => setEditTarget(row)}
                        disabled={committed}
                      >
                        <EditOutlinedIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Remover linha">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => deleteMutation.mutate(row.idx)}
                        disabled={committed || deleteMutation.isPending}
                      >
                        <DeleteOutlineIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Stack>

      {/* Reclassify menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={() => {
          setMenuAnchor(null);
          setMenuRow(null);
        }}
      >
        {ROW_CLASS_OPTIONS.map((cls) => (
          <MenuItem
            key={cls}
            selected={menuRow?.row_class === cls}
            onClick={() => {
              if (menuRow) classifyMutation.mutate({ rowIdx: menuRow.idx, row_class: cls });
            }}
          >
            {cls}
          </MenuItem>
        ))}
      </Menu>

      {/* Edit dialog */}
      <RowEditDialog
        open={Boolean(editTarget)}
        row={editTarget}
        onClose={() => setEditTarget(null)}
        onSave={handleSaveEdit}
        loading={editMutation.isPending}
      />

      {/* Add dialog — reuses RowEditDialog with an empty row */}
      <RowEditDialog
        open={addMode}
        row={{ idx: -1, sheet_row: null, row_class: 'ITEM', codigo: null, descricao: null, unidade: null, quantidade: null, preco: null, valor: null }}
        onClose={() => setAddMode(false)}
        onSave={handleSaveAdd}
        loading={addMutation.isPending}
      />
    </>
  );
}
```

- [ ] **Step 2: Type-check**

```bash
cd app/frontend && npx tsc --noEmit 2>&1 | grep -i "SmartImportStaging\|RowEditDialog\|smartImportApi" | head -20
```

Expected: no output.

- [ ] **Step 3: Commit**

```bash
git add app/frontend/src/features/smart-import/SmartImportStagingPage.tsx
git commit -m "feat(smart-import/phase-c): add SmartImportStagingPage with row edit/delete/classify/commit"
```

---

## Task C5: Routes + Router Registration

**Files:**
- Create: `app/frontend/src/features/smart-import/routes.tsx`
- Modify: `app/frontend/src/app/router.tsx`

- [ ] **Step 1: Create route declarations**

```tsx
// app/frontend/src/features/smart-import/routes.tsx
import { lazy } from 'react';
import { Route } from 'react-router-dom';

const SmartImportUploadPage = lazy(() =>
  import('./SmartImportUploadPage').then((m) => ({ default: m.SmartImportUploadPage })),
);

const SmartImportStagingPage = lazy(() =>
  import('./SmartImportStagingPage').then((m) => ({ default: m.SmartImportStagingPage })),
);

export const smartImportRoutes = (
  <Route path="smart-import">
    <Route path="upload" element={<SmartImportUploadPage />} />
    <Route path=":jobId" element={<SmartImportStagingPage />} />
  </Route>
);
```

- [ ] **Step 2: Register routes in router.tsx**

In `app/frontend/src/app/router.tsx`, add the import at the top (alongside the existing proposal routes import):

```tsx
import { smartImportRoutes } from '../features/smart-import/routes';
```

Inside the `<Route element={<AuthenticatedApp />}>` block, add after the `/bcu/de-para` route:

```tsx
{smartImportRoutes}
```

The final block in `AuthenticatedApp` should look like:

```tsx
<Route element={<AuthenticatedApp />}>
  <Route index element={<Navigate to="/dashboard" replace />} />
  <Route path="/dashboard" element={<DashboardPage />} />
  <Route path="/busca" element={<SearchPage />} />
  <Route path="/servicos" element={<ServicesPage />} />
  <Route path="/homologacao" element={<HomologationPage />} />
  <Route path="/composicoes" element={<CompositionsPage />} />
  <Route path="/associacoes" element={<AssociationsPage />} />
  <Route path="/relatorios" element={<ReportsPage />} />
  <Route path="/extracao" element={<ExtractionPage />} />
  <Route path="/bcu" element={<BcuPage />} />
  <Route path="/bcu/gestao" element={<BcuGestaoPage />} />
  <Route path="/bcu/upload" element={<BcuUploadPage />} />
  <Route path="/bcu/de-para" element={<BcuDeParaPage />} />
  <Route path="/perfil" element={<ProfilePage />} />

  {proposalRoutes}
  {smartImportRoutes}

  <Route element={<AdminOnlyLayout />}>
    <Route path="/admin" element={<AdminPage />} />
    <Route path="/usuarios" element={<UsersPage />} />
    <Route path="/clientes" element={<ClientsPage />} />
    <Route path="/permissoes" element={<PermissionsPage />} />
  </Route>
</Route>
```

- [ ] **Step 3: Type-check**

```bash
cd app/frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: 0 errors.

- [ ] **Step 4: Commit**

```bash
git add app/frontend/src/features/smart-import/routes.tsx app/frontend/src/app/router.tsx
git commit -m "feat(smart-import/phase-c): register /smart-import/upload and /smart-import/:jobId routes"
```

---

## Task C6: Manual Smoke Test

This is a frontend feature — verify it works in the browser before closing out Phase C.

- [ ] **Step 1: Start the dev server**

```bash
cd app/frontend && npm run dev
```

Expected: Vite dev server starts on `http://localhost:5173` (or configured port).

- [ ] **Step 2: Navigate to upload page**

Open `http://localhost:5173/smart-import/upload` in the browser.

Expected: Page renders with "Smart Import" header, a text field for "ID do Cliente", a file picker button, and a disabled "Importar Planilha" button.

- [ ] **Step 3: Upload a test file**

Use any `.xlsx` file (e.g., one of the sample PQ files from the project). Enter a valid `cliente_id` UUID. Click "Selecionar Arquivo" and pick the file. The submit button should enable. Click "Importar Planilha".

Expected: Loading state appears, then the browser navigates to `/smart-import/<job-uuid>`.

- [ ] **Step 4: Verify staging page**

Expected on `/smart-import/:jobId`:
- Page header shows filename and detected header row
- Table shows rows with colored class chips (ITEM=blue, SECAO=purple, TOTAL=red, VAZIA=grey)
- ITEM rows missing `quantidade` show `⚠ —` in the Qtd column
- Edit icon opens `RowEditDialog` with current values pre-filled
- Clicking a class chip opens reclassify menu

- [ ] **Step 5: Test edit flow**

Click edit on any row. Change the description. Click "Salvar".

Expected: Dialog closes, table refreshes with new description.

- [ ] **Step 6: Test reclassify flow**

Click a class chip on any row. Select a different class from the menu.

Expected: Menu closes, chip color updates to new class.

- [ ] **Step 7: Test commit**

Click "Commitar Importação".

Expected: Loading state, then a green success alert showing confidence score and corrections applied count.

- [ ] **Step 8: Final commit (if any cleanup needed)**

```bash
git add -p  # review any debug/console.log cleanup
git commit -m "feat(smart-import/phase-c): complete frontend staging UI"
```

---

## Self-Review

### Spec Coverage
- [x] File upload (xlsx/csv) → `SmartImportUploadPage`, `smartImportApi.upload`
- [x] Auto-detect (backend handles, frontend shows `detected_header_row`) 
- [x] Staging table with all 6 fields → `SmartImportStagingPage` table
- [x] Edit row → `RowEditDialog` + `smartImportApi.editRow`
- [x] Add row → `RowEditDialog` in add mode + `smartImportApi.addRow`
- [x] Delete row → delete icon + `smartImportApi.deleteRow`
- [x] Reclassify → class chip menu + `smartImportApi.classifyRow`
- [x] Correction tracking → `corrections` state accumulates `ROW_RECLASSIFY` entries
- [x] Commit with corrections → `smartImportApi.commitJob` + success alert with score
- [x] Profile learning feedback → `CommitJobResponse.score_confianca` shown in alert
- [x] Route registration → `/smart-import/upload` + `/smart-import/:jobId`

### Placeholder Scan
No TBD/TODO/placeholder patterns found — all code blocks are complete.

### Type Consistency
- `StagingRow.idx: number` used consistently in `editRow(jobId, rowIdx, patch)`, `deleteRow(jobId, rowIdx)`, `classifyRow(jobId, rowIdx, row_class)`
- `RowPatch` = `Partial<Pick<StagingRow, 'codigo'|'descricao'|'unidade'|'quantidade'|'preco'|'valor'>>` — used in `RowEditDialog.onSave` and `editMutation.mutationFn`
- `CorrectionEntry` interface defined in Task C1, used in `SmartImportStagingPage.corrections` state and `commitJob` call
- `RowClass` union type defined in Task C1, used in `classifyMutation`, `CLASS_CHIP_COLOR`, `ROW_CLASS_OPTIONS`
