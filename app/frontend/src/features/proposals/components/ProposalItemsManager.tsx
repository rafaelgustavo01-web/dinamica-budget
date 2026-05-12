import { useState } from 'react';
import {
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
  CircularProgress,
} from '@mui/material';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import AddIcon from '@mui/icons-material/Add';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type {
  ProposalItem,
  AddItemRequest,
  UpdateItemRequest,
} from '../../../shared/services/api/proposalItemsApi';
import { proposalItemsApi } from '../../../shared/services/api/proposalItemsApi';
import { extractApiErrorMessage } from '../../../shared/services/api/apiClient';

interface ProposalItemsManagerProps {
  propostaId: string;
  propostaStatus: string;
  userRole?: string;
  readOnly?: boolean;
}

export function ProposalItemsManager({
  propostaId,
  propostaStatus,
  userRole,
  readOnly = false,
}: ProposalItemsManagerProps) {
  const queryClient = useQueryClient();
  const [openDialog, setOpenDialog] = useState(false);
  const [editingItem, setEditingItem] = useState<ProposalItem | null>(null);
  const [formData, setFormData] = useState<AddItemRequest>({
    codigo: '',
    descricao: '',
    unidade_medida: 'un',
    quantidade: 1,
  });

  const canEdit = !readOnly && (userRole === 'EDITOR' || userRole === 'OWNER');
  const canAddRemove = canEdit && (propostaStatus === 'RASCUNHO' || propostaStatus === 'CPU_GERADA');
  const canDelete = canEdit && propostaStatus === 'RASCUNHO';

  // Listar items
  const { data: items = [], isLoading, isError, error } = useQuery({
    queryKey: ['proposalItems', propostaId],
    queryFn: () => proposalItemsApi.listItems(propostaId),
    enabled: Boolean(propostaId),
    select: (data): ProposalItem[] => (Array.isArray(data) ? data : []),
  });

  // Adicionar/atualizar item
  const addItemMutation = useMutation({
    mutationFn: (body: AddItemRequest) => proposalItemsApi.addItem(propostaId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposalItems', propostaId] });
      queryClient.invalidateQueries({ queryKey: ['proposta', propostaId] });
      setFormData({ codigo: '', descricao: '', unidade_medida: 'un', quantidade: 1 });
      setOpenDialog(false);
    },
  });

  const updateItemMutation = useMutation({
    mutationFn: ({ itemId, body }: { itemId: string; body: UpdateItemRequest }) =>
      proposalItemsApi.updateItem(propostaId, itemId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposalItems', propostaId] });
      queryClient.invalidateQueries({ queryKey: ['proposta', propostaId] });
      setFormData({ codigo: '', descricao: '', unidade_medida: 'un', quantidade: 1 });
      setEditingItem(null);
      setOpenDialog(false);
    },
  });

  const deleteItemMutation = useMutation({
    mutationFn: (itemId: string) => proposalItemsApi.deleteItem(propostaId, itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposalItems', propostaId] });
      queryClient.invalidateQueries({ queryKey: ['proposta', propostaId] });
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

  const handleSubmit = async () => {
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

  if (isLoading) return <CircularProgress />;

  return (
    <Paper sx={{ p: 3 }}>
      <Stack spacing={2}>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Itens da Proposta</Typography>
          {canAddRemove && !readOnly && (
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => handleOpenDialog()}
            >
              Adicionar Item
            </Button>
          )}
        </Box>

        {isError && (
          <Alert severity="error">{extractApiErrorMessage(error)}</Alert>
        )}

        {!canAddRemove && !readOnly && (
          <Alert severity="info">
            Items podem ser {editingItem ? 'editados' : 'adicionados'} apenas em status RASCUNHO ou CPU_GERADA
          </Alert>
        )}

        {items.length === 0 ? (
          <Alert severity="info">Nenhum item adicionado ainda.</Alert>
        ) : (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                  <TableCell sx={{ fontWeight: 'bold' }}>Ordem</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Código</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Descrição</TableCell>
                  <TableCell align="right" sx={{ fontWeight: 'bold' }}>Qtd</TableCell>
                  <TableCell sx={{ fontWeight: 'bold' }}>Un.</TableCell>
                  {canEdit && <TableCell align="center" sx={{ fontWeight: 'bold' }}>Ações</TableCell>}
                </TableRow>
              </TableHead>
              <TableBody>
                {items.map((item) => (
                  <TableRow key={item.id} hover>
                    <TableCell>{item.ordem ?? '-'}</TableCell>
                    <TableCell>{item.codigo}</TableCell>
                    <TableCell>{item.descricao}</TableCell>
                    <TableCell align="right">{item.quantidade.toFixed(2)}</TableCell>
                    <TableCell>{item.unidade_medida}</TableCell>
                    {canEdit && (
                      <TableCell align="center">
                        {propostaStatus === 'RASCUNHO' && (
                          <IconButton
                            size="small"
                            onClick={() => handleOpenDialog(item)}
                            disabled={updateItemMutation.isPending}
                          >
                            <EditOutlinedIcon fontSize="small" />
                          </IconButton>
                        )}
                        {canDelete && (
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => {
                              if (
                                window.confirm(
                                  `Tem certeza que deseja remover o item "${item.descricao}"?`
                                )
                              ) {
                                deleteItemMutation.mutate(item.id);
                              }
                            }}
                            disabled={deleteItemMutation.isPending}
                          >
                            <DeleteOutlineIcon fontSize="small" />
                          </IconButton>
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

      {/* Dialog para adicionar/editar item */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingItem ? `Editar Item: ${editingItem.descricao}` : 'Adicionar Novo Item'}
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
              placeholder="Ex: 01"
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
              onChange={(e) =>
                setFormData({ ...formData, quantidade: parseFloat(e.target.value) || 1 })
              }
              fullWidth
              size="small"
              inputProps={{ step: '0.01', min: '0' }}
            />
            <TextField
              label="Unidade de Medida"
              value={formData.unidade_medida}
              onChange={(e) =>
                setFormData({ ...formData, unidade_medida: e.target.value })
              }
              fullWidth
              size="small"
              placeholder="Ex: m³, m, un, etc"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={
              addItemMutation.isPending ||
              updateItemMutation.isPending ||
              !formData.codigo ||
              !formData.descricao
            }
          >
            {editingItem ? 'Atualizar' : 'Adicionar'}
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
}
