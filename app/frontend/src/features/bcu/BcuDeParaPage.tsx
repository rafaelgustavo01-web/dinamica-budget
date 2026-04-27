import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Skeleton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
} from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { PageHeader } from '../../shared/components/PageHeader';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import { bcuDeParaApi } from '../../shared/services/api/bcuDeParaApi';
import type { DeParaListItem } from '../../shared/services/api/bcuDeParaApi';

const headCell = {
  fontWeight: 700,
  fontSize: '0.72rem',
  textTransform: 'uppercase' as const,
  color: 'text.secondary',
  whiteSpace: 'nowrap' as const,
  py: 1,
  px: 1.5,
};

const dataCell = {
  fontSize: '0.8rem',
  py: 0.75,
  px: 1.5,
};

const BCU_TYPES = [
  { value: 'MO', label: 'Mão de Obra' },
  { value: 'EQP', label: 'Equipamento' },
  { value: 'EPI', label: 'EPI' },
  { value: 'FER', label: 'Ferramenta' },
];

export function BcuDeParaPage() {
  const { showMessage } = useFeedback();
  const queryClient = useQueryClient();
  const [onlyUnmapped, setOnlyUnmapped] = useState(false);
  const [search, setSearch] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState({ base_tcpo_id: '', bcu_table_type: 'MO', bcu_item_id: '' });

  const { data, isLoading, error } = useQuery({
    queryKey: ['bcu-de-para', onlyUnmapped, search],
    queryFn: () => bcuDeParaApi.listar({ only_unmapped: onlyUnmapped, search: search || undefined }),
  });

  const criarMutation = useMutation({
    mutationFn: bcuDeParaApi.criar,
    onSuccess: () => {
      setDialogOpen(false);
      void queryClient.invalidateQueries({ queryKey: ['bcu-de-para'] });
      showMessage('Mapeamento criado com sucesso.');
    },
    onError: (err) => showMessage(extractApiErrorMessage(err, 'Erro ao criar mapeamento.'), 'error'),
  });

  const atualizarMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Parameters<typeof bcuDeParaApi.atualizar>[1] }) =>
      bcuDeParaApi.atualizar(id, payload),
    onSuccess: () => {
      setDialogOpen(false);
      setEditingId(null);
      void queryClient.invalidateQueries({ queryKey: ['bcu-de-para'] });
      showMessage('Mapeamento atualizado com sucesso.');
    },
    onError: (err) => showMessage(extractApiErrorMessage(err, 'Erro ao atualizar mapeamento.'), 'error'),
  });

  const deletarMutation = useMutation({
    mutationFn: bcuDeParaApi.deletar,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['bcu-de-para'] });
      showMessage('Mapeamento removido com sucesso.');
    },
    onError: (err) => showMessage(extractApiErrorMessage(err, 'Erro ao remover mapeamento.'), 'error'),
  });

  const openCreate = () => {
    setEditingId(null);
    setForm({ base_tcpo_id: '', bcu_table_type: 'MO', bcu_item_id: '' });
    setDialogOpen(true);
  };

  const openEdit = (item: DeParaListItem) => {
    setEditingId(item.id);
    setForm({
      base_tcpo_id: item.base_tcpo_id,
      bcu_table_type: item.bcu_table_type ?? 'MO',
      bcu_item_id: item.bcu_item_id ?? '',
    });
    setDialogOpen(true);
  };

  const handleSubmit = () => {
    const payload = {
      base_tcpo_id: form.base_tcpo_id,
      bcu_table_type: form.bcu_table_type,
      bcu_item_id: form.bcu_item_id,
    };
    if (editingId) {
      atualizarMutation.mutate({ id: editingId, payload });
    } else {
      criarMutation.mutate(payload);
    }
  };

  return (
    <Box>
      <PageHeader
        title="De/Para BCU ↔ BaseTcpo"
        description="Mapeie insumos da base TCPO para itens correspondentes na BCU para composição de custos."
      />

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems="center" sx={{ mb: 2 }}>
        <TextField
          size="small"
          placeholder="Buscar descrição..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{ minWidth: 260 }}
        />
        <Button variant={onlyUnmapped ? 'contained' : 'outlined'} onClick={() => setOnlyUnmapped((v) => !v)}>
          {onlyUnmapped ? 'Mostrando não mapeados' : 'Mostrar não mapeados'}
        </Button>
        <Box flex={1} />
        <Button variant="contained" onClick={openCreate}>
          Novo Mapeamento
        </Button>
      </Stack>

      {isLoading && (
        <Stack spacing={1}>
          <Skeleton variant="rectangular" height={40} />
          <Skeleton variant="rectangular" height={300} />
        </Stack>
      )}

      {error && <Alert severity="error">Erro ao carregar mapeamentos.</Alert>}

      {!isLoading && !error && data && (
        <Paper variant="outlined">
          <TableContainer>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell sx={headCell}>Código TCPO</TableCell>
                  <TableCell sx={headCell}>Descrição TCPO</TableCell>
                  <TableCell sx={headCell}>Tipo</TableCell>
                  <TableCell sx={headCell}>BCU Tipo</TableCell>
                  <TableCell sx={headCell}>BCU Item</TableCell>
                  <TableCell sx={headCell}>BCU Descrição</TableCell>
                  <TableCell sx={headCell} align="right">Ações</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} sx={{ ...dataCell, textAlign: 'center', py: 4 }}>
                      Nenhum registro encontrado.
                    </TableCell>
                  </TableRow>
                )}
                {data.map((item) => (
                  <TableRow key={item.id ?? item.base_tcpo_id} hover>
                    <TableCell sx={dataCell}>{item.base_tcpo_codigo}</TableCell>
                    <TableCell sx={dataCell}>{item.base_tcpo_descricao}</TableCell>
                    <TableCell sx={dataCell}>
                      <Chip label={item.base_tcpo_tipo_recurso ?? '—'} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell sx={dataCell}>
                      {item.bcu_table_type ? (
                        <Chip label={item.bcu_table_type} size="small" color="primary" />
                      ) : (
                        '—'
                      )}
                    </TableCell>
                    <TableCell sx={dataCell}>{item.bcu_item_id ?? '—'}</TableCell>
                    <TableCell sx={dataCell}>{item.bcu_item_descricao ?? '—'}</TableCell>
                    <TableCell sx={dataCell} align="right">
                      <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                        {item.id && (
                          <>
                            <Button size="small" startIcon={<EditOutlinedIcon />} onClick={() => openEdit(item)}>
                              Editar
                            </Button>
                            <Button
                              size="small"
                              color="error"
                              startIcon={<DeleteOutlineIcon />}
                              onClick={() => deletarMutation.mutate(item.id!)}
                            >
                              Remover
                            </Button>
                          </>
                        )}
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingId ? 'Editar Mapeamento' : 'Novo Mapeamento'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="BaseTcpo ID"
              value={form.base_tcpo_id}
              onChange={(e) => setForm((f) => ({ ...f, base_tcpo_id: e.target.value }))}
              fullWidth
              disabled={!!editingId}
            />
            <FormControl fullWidth>
              <InputLabel>Tipo BCU</InputLabel>
              <Select
                value={form.bcu_table_type}
                label="Tipo BCU"
                onChange={(e) => setForm((f) => ({ ...f, bcu_table_type: e.target.value }))}
              >
                {BCU_TYPES.map((t) => (
                  <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="BCU Item ID"
              value={form.bcu_item_id}
              onChange={(e) => setForm((f) => ({ ...f, bcu_item_id: e.target.value }))}
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={criarMutation.isPending || atualizarMutation.isPending}
          >
            Salvar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
