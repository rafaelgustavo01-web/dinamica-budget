import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  CircularProgress,
  Paper,
  Stack,
  Typography,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Box,
  Alert,
  Container,
  Card,
  CardContent,
  Chip,
} from '@mui/material';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import AddIcon from '@mui/icons-material/Add';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import RefreshIcon from '@mui/icons-material/Refresh';

import { PageHeader } from '../../../shared/components/PageHeader';
import { proposalsApi } from '../../../shared/services/api/proposalsApi';
import type {
  ProposalItem,
  AddItemRequest,
  UpdateItemRequest,
} from '../../../shared/services/api/proposalItemsApi';
import { proposalItemsApi } from '../../../shared/services/api/proposalItemsApi';

export function ProposalItemsPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [openDialog, setOpenDialog] = useState(false);
  const [editingItem, setEditingItem] = useState<ProposalItem | null>(null);
  const [formData, setFormData] = useState<AddItemRequest>({
    codigo: '',
    descricao: '',
    unidade_medida: 'un',
    quantidade: 1,
  });

  // Buscar proposta
  const { data: proposta, isLoading: isLoadingProposta } = useQuery({
    queryKey: ['proposta', id],
    queryFn: () => proposalsApi.getById(id!),
    enabled: Boolean(id),
  });

  // Listar items
  const { data: items = [], isLoading: isLoadingItems, refetch } = useQuery({
    queryKey: ['proposalItems', id],
    queryFn: () => proposalItemsApi.listItems(id!),
    enabled: Boolean(id),
  });

  // Adicionar item
  const addItemMutation = useMutation({
    mutationFn: (body: AddItemRequest) => proposalItemsApi.addItem(id!, body),
    onSuccess: () => {
      refetch();
      queryClient.invalidateQueries({ queryKey: ['proposta', id] });
      setFormData({ codigo: '', descricao: '', unidade_medida: 'un', quantidade: 1 });
      setOpenDialog(false);
    },
  });

  // Atualizar item
  const updateItemMutation = useMutation({
    mutationFn: ({ itemId, body }: { itemId: string; body: UpdateItemRequest }) =>
      proposalItemsApi.updateItem(id!, itemId, body),
    onSuccess: () => {
      refetch();
      queryClient.invalidateQueries({ queryKey: ['proposta', id] });
      setFormData({ codigo: '', descricao: '', unidade_medida: 'un', quantidade: 1 });
      setEditingItem(null);
      setOpenDialog(false);
    },
  });

  // Remover item
  const deleteItemMutation = useMutation({
    mutationFn: (itemId: string) => proposalItemsApi.deleteItem(id!, itemId),
    onSuccess: () => {
      refetch();
      queryClient.invalidateQueries({ queryKey: ['proposta', id] });
    },
  });

  const handleOpenDialog = (item?: ProposalItem) => {
    if (item) {
      setEditingItem(item);
      setFormData({
        codigo: item.codigo,
        descricao: item.descricao,
        unidade_medida: item.unidade_medida,
        quantidade: item.quantidade,
      });
    } else {
      setEditingItem(null);
      setFormData({ codigo: '', descricao: '', unidade_medida: 'un', quantidade: 1 });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingItem(null);
    setFormData({ codigo: '', descricao: '', unidade_medida: 'un', quantidade: 1 });
  };

  const handleSubmit = () => {
    if (!formData.codigo || !formData.descricao) {
      alert('Código e descrição são obrigatórios');
      return;
    }

    if (editingItem) {
      updateItemMutation.mutate({
        itemId: editingItem.id,
        body: {
          descricao: formData.descricao,
          quantidade: formData.quantidade,
          unidade_medida: formData.unidade_medida,
        },
      });
    } else {
      addItemMutation.mutate(formData);
    }
  };

  const canEdit = proposta?.status === 'RASCUNHO' || proposta?.status === 'CPU_GERADA';
  const isLoadingAll = isLoadingProposta || isLoadingItems;

  return (
    <>
      <PageHeader
        title={proposta ? `Itens: ${proposta.codigo}` : 'Itens da Proposta'}
        description={proposta?.titulo || ''}
        actions={
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              startIcon={<ArrowBackIcon />}
              onClick={() => navigate(`/propostas/${id}`)}
            >
              Voltar
            </Button>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => refetch()}
              disabled={isLoadingAll}
            >
              Atualizar
            </Button>
            {canEdit && (
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => handleOpenDialog()}
                disabled={isLoadingAll || addItemMutation.isPending}
              >
                Novo Item
              </Button>
            )}
          </Stack>
        }
      />

      <Container maxWidth="lg" sx={{ py: 3 }}>
        <Stack spacing={3}>
          {/* Status */}
          {proposta && (
            <Card>
              <CardContent>
                <Stack direction="row" spacing={2}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Status</Typography>
                    <Typography variant="body2">{proposta.status}</Typography>
                  </Box>
                  {proposta.cpu_desatualizada && (
                    <Box>
                      <Chip label="CPU Desatualizada" color="warning" size="small" />
                    </Box>
                  )}
                </Stack>
              </CardContent>
            </Card>
          )}

          {/* Avisos */}
          {!canEdit && proposta && (
            <Alert severity="info">
              Items podem ser adicionados apenas em status RASCUNHO ou CPU_GERADA. Status atual: <strong>{proposta.status}</strong>
            </Alert>
          )}

          {/* Tabela de Items */}
          {isLoadingAll ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
              <CircularProgress />
            </Box>
          ) : items.length === 0 ? (
            <Alert severity="info">Nenhum item adicionado ainda. {canEdit && 'Clique em "Novo Item" para adicionar.'}</Alert>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                    <TableCell sx={{ fontWeight: 'bold' }}>Ordem</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Código</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Descrição</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'bold' }}>Qtd</TableCell>
                    <TableCell sx={{ fontWeight: 'bold' }}>Unidade</TableCell>
                    {canEdit && <TableCell align="center" sx={{ fontWeight: 'bold' }}>Ações</TableCell>}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {items.map((item) => (
                    <TableRow key={item.id} hover>
                      <TableCell>{item.ordem ?? '-'}</TableCell>
                      <TableCell><strong>{item.codigo}</strong></TableCell>
                      <TableCell>{item.descricao}</TableCell>
                      <TableCell align="right">{item.quantidade.toFixed(2)}</TableCell>
                      <TableCell>{item.unidade_medida}</TableCell>
                      {canEdit && (
                        <TableCell align="center">
                          {proposta?.status === 'RASCUNHO' && (
                            <>
                              <IconButton
                                size="small"
                                onClick={() => handleOpenDialog(item)}
                                disabled={updateItemMutation.isPending}
                              >
                                <EditOutlinedIcon fontSize="small" />
                              </IconButton>
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => {
                                  if (window.confirm(`Remover item "${item.descricao}"?`)) {
                                    deleteItemMutation.mutate(item.id);
                                  }
                                }}
                                disabled={deleteItemMutation.isPending}
                              >
                                <DeleteOutlineIcon fontSize="small" />
                              </IconButton>
                            </>
                          )}
                        </TableCell>
                      )}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Stack>
      </Container>

      {/* Dialog para adicionar/editar */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingItem ? `Editar: ${editingItem.descricao}` : 'Novo Item'}
        </DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <Stack spacing={2}>
            <TextField
              label="Código"
              value={formData.codigo}
              onChange={(e) => setFormData({ ...formData, codigo: e.target.value })}
              disabled={Boolean(editingItem)}
              fullWidth
              size="small"
              placeholder="01, 02, etc"
            />
            <TextField
              label="Descrição"
              value={formData.descricao}
              onChange={(e) => setFormData({ ...formData, descricao: e.target.value })}
              fullWidth
              size="small"
              multiline
              rows={3}
              placeholder="Ex: Escavação em solo"
            />
            <TextField
              label="Quantidade"
              type="number"
              value={formData.quantidade}
              onChange={(e) => setFormData({ ...formData, quantidade: parseFloat(e.target.value) || 1 })}
              fullWidth
              size="small"
              inputProps={{ step: '0.01', min: '0' }}
            />
            <TextField
              label="Unidade"
              value={formData.unidade_medida}
              onChange={(e) => setFormData({ ...formData, unidade_medida: e.target.value })}
              fullWidth
              size="small"
              placeholder="m³, m, un, etc"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={addItemMutation.isPending || updateItemMutation.isPending || !formData.codigo || !formData.descricao}
          >
            {editingItem ? 'Atualizar' : 'Adicionar'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
