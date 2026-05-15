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

const EMPTY_ROW: StagingRow = {
  idx: -1,
  sheet_row: null,
  row_class: 'ITEM',
  codigo: null,
  descricao: null,
  unidade: null,
  quantidade: null,
  preco: null,
  valor: null,
};

export function SmartImportStagingPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [corrections, setCorrections] = useState<CorrectionEntry[]>([]);
  const [editTarget, setEditTarget] = useState<StagingRow | null>(null);
  const [addMode, setAddMode] = useState(false);
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
    onSuccess: () => {
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
      codigo: patch.codigo ?? null,
      unidade: patch.unidade ?? null,
      quantidade: patch.quantidade ?? null,
      preco: patch.preco ?? null,
      valor: patch.valor ?? null,
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
        {job.status === 'REVIEW_REQUIRED' && job.has_warnings && !commitMutation.isSuccess && (
          <Alert severity="warning">
            Algumas linhas precisam de revisão. Verifique itens sem quantidade ou descrição.
          </Alert>
        )}

        {commitMutation.isSuccess && (
          <Alert
            severity="success"
            icon={<CheckCircleOutlineIcon />}
            action={
              job.proposta_id ? (
                <Button
                  color="inherit"
                  size="small"
                  onClick={() => navigate(`/propostas/${job.proposta_id}/match-review`)}
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

        {commitMutation.isError && (
          <Alert severity="error">{extractApiErrorMessage(commitMutation.error)}</Alert>
        )}

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
            onClick={() => commitMutation.mutate()}
          >
            Commitar Importação
          </Button>
        </Stack>

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

      <RowEditDialog
        open={Boolean(editTarget)}
        row={editTarget}
        onClose={() => setEditTarget(null)}
        onSave={handleSaveEdit}
        loading={editMutation.isPending}
      />

      <RowEditDialog
        open={addMode}
        row={EMPTY_ROW}
        onClose={() => setAddMode(false)}
        onSave={handleSaveAdd}
        loading={addMutation.isPending}
      />
    </>
  );
}
