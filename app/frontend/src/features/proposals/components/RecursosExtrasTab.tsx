import { useState } from 'react';
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { RecursoExtraCreate, RecursoExtraOut, RecursoExtraUpdate } from '../../../shared/types/contracts/proposta_pc';
import { histogramaApi } from '../../../shared/services/api/histogramaApi';

interface Props {
  propostaId: string;
}

const headCell = { fontWeight: 700, fontSize: '0.72rem', textTransform: 'uppercase' as const, color: 'text.secondary', whiteSpace: 'nowrap' as const, py: 1, px: 1.5 };
const dataCell = { fontSize: '0.8rem', py: 0.75, px: 1.5 };

export function RecursosExtrasTab({ propostaId }: Props) {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<RecursoExtraCreate>({ tipo_recurso: 'INSUMO', descricao: '', custo_unitario: 0 });

  const { data: extras, isLoading } = useQuery({
    queryKey: ['recursos-extras', propostaId],
    queryFn: () => histogramaApi.listarRecursosExtras(propostaId),
  });

  const criarMutation = useMutation({
    mutationFn: (payload: RecursoExtraCreate) => histogramaApi.criarRecursoExtra(propostaId, payload),
    onSuccess: () => {
      setDialogOpen(false);
      resetForm();
      void queryClient.invalidateQueries({ queryKey: ['recursos-extras', propostaId] });
      void queryClient.invalidateQueries({ queryKey: ['histograma', propostaId] });
    },
  });

  const atualizarMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: RecursoExtraUpdate }) =>
      histogramaApi.atualizarRecursoExtra(propostaId, id, payload),
    onSuccess: () => {
      setDialogOpen(false);
      setEditingId(null);
      resetForm();
      void queryClient.invalidateQueries({ queryKey: ['recursos-extras', propostaId] });
    },
  });

  const deletarMutation = useMutation({
    mutationFn: (id: string) => histogramaApi.deletarRecursoExtra(propostaId, id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['recursos-extras', propostaId] });
      void queryClient.invalidateQueries({ queryKey: ['histograma', propostaId] });
    },
  });

  const resetForm = () => setForm({ tipo_recurso: 'INSUMO', descricao: '', custo_unitario: 0 });

  const openCreate = () => {
    setEditingId(null);
    resetForm();
    setDialogOpen(true);
  };

  const openEdit = (extra: RecursoExtraOut) => {
    setEditingId(extra.id);
    setForm({
      tipo_recurso: extra.tipo_recurso,
      descricao: extra.descricao,
      unidade_medida: extra.unidade_medida,
      custo_unitario: extra.custo_unitario,
      observacao: extra.observacao,
    });
    setDialogOpen(true);
  };

  const handleSubmit = () => {
    if (editingId) {
      atualizarMutation.mutate({ id: editingId, payload: form });
    } else {
      criarMutation.mutate(form);
    }
  };

  return (
    <Box>
      <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="subtitle1" fontWeight={600}>
          Recursos Extras ({extras?.length ?? 0})
        </Typography>
        <Box flex={1} />
        <Button variant="contained" size="small" startIcon={<AddIcon />} onClick={openCreate}>
          Novo Recurso
        </Button>
      </Stack>

      {isLoading && <Typography variant="body2" color="text.secondary">Carregando...</Typography>}

      {!isLoading && (!extras || extras.length === 0) && (
        <Typography variant="body2" color="text.secondary">
          Nenhum recurso extra cadastrado. Adicione recursos que não estão no catálogo BCU.
        </Typography>
      )}

      {extras && extras.length > 0 && (
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={headCell}>Descrição</TableCell>
                <TableCell sx={headCell}>Tipo</TableCell>
                <TableCell sx={headCell}>Unidade</TableCell>
                <TableCell sx={{ ...headCell, textAlign: 'right' }}>Custo Unit.</TableCell>
                <TableCell sx={{ ...headCell, textAlign: 'center' }}>Alocações</TableCell>
                <TableCell sx={headCell} align="right">Ações</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {extras.map((extra) => (
                <TableRow key={extra.id} hover>
                  <TableCell sx={dataCell}>
                    <Typography variant="body2" fontWeight={500}>{extra.descricao}</Typography>
                    {extra.observacao && (
                      <Typography variant="caption" color="text.secondary">{extra.observacao}</Typography>
                    )}
                  </TableCell>
                  <TableCell sx={dataCell}>
                    <Chip label={extra.tipo_recurso} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell sx={dataCell}>{extra.unidade_medida ?? '—'}</TableCell>
                  <TableCell sx={{ ...dataCell, textAlign: 'right' }}>
                    R$ {extra.custo_unitario.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </TableCell>
                  <TableCell sx={{ ...dataCell, textAlign: 'center' }}>
                    {extra.alocacoes_count > 0 ? (
                      <Chip label={String(extra.alocacoes_count)} size="small" color="primary" />
                    ) : (
                      '—'
                    )}
                  </TableCell>
                  <TableCell sx={dataCell} align="right">
                    <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                      <IconButton size="small" onClick={() => openEdit(extra)}>
                        <EditOutlinedIcon fontSize="small" />
                      </IconButton>
                      <IconButton size="small" color="error" onClick={() => deletarMutation.mutate(extra.id)}>
                        <DeleteOutlineIcon fontSize="small" />
                      </IconButton>
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingId ? 'Editar Recurso Extra' : 'Novo Recurso Extra'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Descrição"
              value={form.descricao}
              onChange={(e) => setForm((f) => ({ ...f, descricao: e.target.value }))}
              fullWidth
              required
            />
            <TextField
              label="Tipo de Recurso"
              value={form.tipo_recurso}
              onChange={(e) => setForm((f) => ({ ...f, tipo_recurso: e.target.value }))}
              fullWidth
              required
            />
            <TextField
              label="Unidade de Medida"
              value={form.unidade_medida ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, unidade_medida: e.target.value || null }))}
              fullWidth
            />
            <TextField
              label="Custo Unitário"
              type="number"
              value={form.custo_unitario}
              onChange={(e) => setForm((f) => ({ ...f, custo_unitario: parseFloat(e.target.value) || 0 }))}
              fullWidth
              required
            />
            <TextField
              label="Observação"
              value={form.observacao ?? ''}
              onChange={(e) => setForm((f) => ({ ...f, observacao: e.target.value || null }))}
              fullWidth
              multiline
              rows={2}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancelar</Button>
          <Button variant="contained" onClick={handleSubmit} disabled={!form.descricao || form.custo_unitario < 0}>
            Salvar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
