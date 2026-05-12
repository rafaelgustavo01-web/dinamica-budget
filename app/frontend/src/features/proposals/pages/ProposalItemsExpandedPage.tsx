import { useState, useMemo } from 'react';
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
  IconButton,
  Box,
  Alert,
  Container,
  Card,
  CardContent,
  Chip,
  Autocomplete,
} from '@mui/material';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import AddIcon from '@mui/icons-material/Add';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import RefreshIcon from '@mui/icons-material/Refresh';
import CheckIcon from '@mui/icons-material/Check';
import CloseIcon from '@mui/icons-material/Close';

import { PageHeader } from '../../../shared/components/PageHeader';
import { proposalsApi } from '../../../shared/services/api/proposalsApi';
import type {
  BcuItem,
  AddBcuItemRequest,
} from '../../../shared/services/api/proposalItemsApi';
import { proposalItemsApi } from '../../../shared/services/api/proposalItemsApi';

type ItemType = 'generico' | 'mao_obra' | 'epi' | 'equipamento' | 'ferramenta';

interface NewItemRowState {
  isOpen: boolean;
  tipo: ItemType;
  selectedItem: BcuItem | null;
  quantidade: number;
  calculatedTotal: number;
}

export function ProposalItemsExpandedPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [newItemRow, setNewItemRow] = useState<NewItemRowState>({
    isOpen: false,
    tipo: 'mao_obra',
    selectedItem: null,
    quantidade: 1,
    calculatedTotal: 0,
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
    select: (data) => (Array.isArray(data) ? data : []),
  });

  // Listar mão de obra (sempre carregado para busca inline)
  const { data: maoObraItems = [] } = useQuery({
    queryKey: ['bcu.mao_obra', id],
    queryFn: () => proposalItemsApi.listMaoObra(id!),
    enabled: Boolean(id),
    select: (data) => (Array.isArray(data) ? data : []),
  });

  // Listar EPI
  const { data: epiItems = [] } = useQuery({
    queryKey: ['bcu.epi', id],
    queryFn: () => proposalItemsApi.listEpi(id!),
    enabled: Boolean(id),
    select: (data) => (Array.isArray(data) ? data : []),
  });

  // Listar equipamento
  const { data: equipamentoItems = [] } = useQuery({
    queryKey: ['bcu.equipamento', id],
    queryFn: () => proposalItemsApi.listEquipamento(id!),
    enabled: Boolean(id),
    select: (data) => (Array.isArray(data) ? data : []),
  });

  // Listar ferramenta
  const { data: ferramentaItems = [] } = useQuery({
    queryKey: ['bcu.ferramenta', id],
    queryFn: () => proposalItemsApi.listFerramenta(id!),
    enabled: Boolean(id),
    select: (data) => (Array.isArray(data) ? data : []),
  });

  // Adicionar mão de obra
  const addMaoObraMutation = useMutation({
    mutationFn: (body: AddBcuItemRequest) => proposalItemsApi.addMaoObra(id!, body),
    onSuccess: () => {
      refetch();
      queryClient.invalidateQueries({ queryKey: ['proposta', id] });
      setNewItemRow({
        isOpen: false,
        tipo: 'mao_obra',
        selectedItem: null,
        quantidade: 1,
        calculatedTotal: 0,
      });
    },
  });

  // Adicionar EPI
  const addEpiMutation = useMutation({
    mutationFn: (body: AddBcuItemRequest) => proposalItemsApi.addEpi(id!, body),
    onSuccess: () => {
      refetch();
      queryClient.invalidateQueries({ queryKey: ['proposta', id] });
      setNewItemRow({
        isOpen: false,
        tipo: 'epi',
        selectedItem: null,
        quantidade: 1,
        calculatedTotal: 0,
      });
    },
  });

  // Adicionar equipamento
  const addEquipamentoMutation = useMutation({
    mutationFn: (body: AddBcuItemRequest) => proposalItemsApi.addEquipamento(id!, body),
    onSuccess: () => {
      refetch();
      queryClient.invalidateQueries({ queryKey: ['proposta', id] });
      setNewItemRow({
        isOpen: false,
        tipo: 'equipamento',
        selectedItem: null,
        quantidade: 1,
        calculatedTotal: 0,
      });
    },
  });

  // Adicionar ferramenta
  const addFerramentaMutation = useMutation({
    mutationFn: (body: AddBcuItemRequest) => proposalItemsApi.addFerramenta(id!, body),
    onSuccess: () => {
      refetch();
      queryClient.invalidateQueries({ queryKey: ['proposta', id] });
      setNewItemRow({
        isOpen: false,
        tipo: 'ferramenta',
        selectedItem: null,
        quantidade: 1,
        calculatedTotal: 0,
      });
    },
  });

  // Remover item
  const deleteItemMutation = useMutation({
    mutationFn: (itemId: string) => proposalItemsApi.deleteItem(id!, itemId),
    onSuccess: () => refetch(),
  });

  const handleOpenNewItemRow = (tipo: ItemType) => {
    setNewItemRow({
      isOpen: true,
      tipo,
      selectedItem: null,
      quantidade: 1,
      calculatedTotal: 0,
    });
  };

  const handleCloseNewItemRow = () => {
    setNewItemRow({
      isOpen: false,
      tipo: 'mao_obra',
      selectedItem: null,
      quantidade: 1,
      calculatedTotal: 0,
    });
  };

  const handleSelectItemInRow = (item: BcuItem | null) => {
    setNewItemRow(prev => ({
      ...prev,
      selectedItem: item,
      calculatedTotal: item ? item.valor * prev.quantidade : 0,
    }));
  };

  const handleQuantityChange = (newQuantity: number) => {
    setNewItemRow(prev => ({
      ...prev,
      quantidade: newQuantity,
      calculatedTotal: prev.selectedItem ? prev.selectedItem.valor * newQuantity : 0,
    }));
  };

  const handleConfirmNewItem = async () => {
    if (!newItemRow.selectedItem) {
      alert('Selecione um item');
      return;
    }

    if (newItemRow.quantidade <= 0) {
      alert('Quantidade deve ser maior que 0');
      return;
    }

    const payload: AddBcuItemRequest = {
      bcu_item_id: newItemRow.selectedItem.id,
      quantidade: newItemRow.quantidade,
    };

    try {
      if (newItemRow.tipo === 'mao_obra') {
        await addMaoObraMutation.mutateAsync(payload);
      } else if (newItemRow.tipo === 'epi') {
        await addEpiMutation.mutateAsync(payload);
      } else if (newItemRow.tipo === 'equipamento') {
        await addEquipamentoMutation.mutateAsync(payload);
      } else if (newItemRow.tipo === 'ferramenta') {
        await addFerramentaMutation.mutateAsync(payload);
      }
    } catch (error) {
      alert('Erro ao adicionar item: ' + (error instanceof Error ? error.message : 'Desconhecido'));
    }
  };

  const isLoading = isLoadingProposta || isLoadingItems;
  const isSubmitting =
    addMaoObraMutation.isPending ||
    addEpiMutation.isPending ||
    addEquipamentoMutation.isPending ||
    addFerramentaMutation.isPending ||
    deleteItemMutation.isPending;

  // Retorna a lista de items BCU baseado no tipo selecionado
  const getBcuItemsForType = (tipo: ItemType): BcuItem[] => {
    switch (tipo) {
      case 'mao_obra':
        return maoObraItems;
      case 'epi':
        return epiItems;
      case 'equipamento':
        return equipamentoItems;
      case 'ferramenta':
        return ferramentaItems;
      default:
        return [];
    }
  };

  const bcuItemsForCurrentType = useMemo(
    () => getBcuItemsForType(newItemRow.tipo),
    [newItemRow.tipo, maoObraItems, epiItems, equipamentoItems, ferramentaItems]
  );

  if (isLoading) {
    return <CircularProgress />;
  }

  if (isLoading) {
    return <CircularProgress />;
  }

  if (!proposta) {
    return <Alert severity="error">Proposta não encontrada</Alert>;
  }

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <PageHeader
        title={`Gerenciar Items - ${proposta.codigo}`}
        description={`${proposta.titulo || 'Sem título'}`}
      />

      <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
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
        >
          Atualizar
        </Button>
      </Stack>

      {/* Status Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stack direction="row" spacing={2}>
            <Box>
              <Typography variant="body2" color="textSecondary">
                Status da Proposta
              </Typography>
              <Chip label={proposta.status} color="primary" variant="outlined" />
            </Box>
            <Box>
              <Typography variant="body2" color="textSecondary">
                Total de Items
              </Typography>
              <Typography variant="h6">{items.length} items</Typography>
            </Box>
          </Stack>
        </CardContent>
      </Card>

      {/* Items Table */}
      {items.length > 0 || newItemRow.isOpen ? (
        <TableContainer component={Paper} sx={{ mb: 3 }}>
          <Table>
            <TableHead>
              <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                <TableCell>Código</TableCell>
                <TableCell>Descrição</TableCell>
                <TableCell align="right">Quantidade</TableCell>
                <TableCell>Unidade</TableCell>
                <TableCell align="right">Valor Unitário</TableCell>
                <TableCell align="right">Valor Total</TableCell>
                <TableCell align="center">Ações</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {items.map(item => (
                <TableRow key={item.id} hover>
                  <TableCell>{item.codigo}</TableCell>
                  <TableCell>{item.descricao}</TableCell>
                  <TableCell align="right">{item.quantidade.toFixed(2)}</TableCell>
                  <TableCell>{item.unidade_medida}</TableCell>
                  <TableCell align="right">
                    {item.valor_unitario?.toLocaleString('pt-BR', {
                      style: 'currency',
                      currency: 'BRL',
                    })}
                  </TableCell>
                  <TableCell align="right">
                    {item.valor_total?.toLocaleString('pt-BR', {
                      style: 'currency',
                      currency: 'BRL',
                    })}
                  </TableCell>
                  <TableCell align="center">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => deleteItemMutation.mutate(item.id)}
                      disabled={isSubmitting}
                    >
                      <DeleteOutlineIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}

              {/* Nova linha inline */}
              {newItemRow.isOpen && (
                <TableRow sx={{ backgroundColor: '#e3f2fd' }}>
                  <TableCell colSpan={7}>
                    <Stack spacing={2} sx={{ py: 2 }}>
                      {/* Selector de tipo */}
                      <Stack direction="row" spacing={1}>
                        <Button
                          size="small"
                          variant={newItemRow.tipo === 'mao_obra' ? 'contained' : 'outlined'}
                          onClick={() => {
                            handleOpenNewItemRow('mao_obra');
                          }}
                        >
                          Mão de Obra
                        </Button>
                        <Button
                          size="small"
                          variant={newItemRow.tipo === 'epi' ? 'contained' : 'outlined'}
                          onClick={() => {
                            handleOpenNewItemRow('epi');
                          }}
                        >
                          EPI
                        </Button>
                        <Button
                          size="small"
                          variant={newItemRow.tipo === 'equipamento' ? 'contained' : 'outlined'}
                          onClick={() => {
                            handleOpenNewItemRow('equipamento');
                          }}
                        >
                          Equipamento
                        </Button>
                        <Button
                          size="small"
                          variant={newItemRow.tipo === 'ferramenta' ? 'contained' : 'outlined'}
                          onClick={() => {
                            handleOpenNewItemRow('ferramenta');
                          }}
                        >
                          Ferramenta
                        </Button>
                      </Stack>

                      {/* Autocomplete + Quantidade + Cálculo */}
                      <Stack direction="row" spacing={2} sx={{ alignItems: 'flex-start' }}>
                        {/* Autocomplete para selecionar item */}
                        <Autocomplete
                          sx={{ flex: 1 }}
                          options={bcuItemsForCurrentType}
                          getOptionLabel={option => `${option.codigo} - ${option.descricao}`}
                          value={newItemRow.selectedItem}
                          onChange={(_, newValue) => handleSelectItemInRow(newValue)}
                          renderInput={params => (
                            <TextField
                              {...params}
                              label="Selecionar item..."
                              placeholder="Digite para buscar"
                            />
                          )}
                          loading={false}
                          noOptionsText="Nenhum item encontrado"
                        />

                        {/* Quantidade */}
                        <TextField
                          label="Qtd"
                          type="number"
                          value={newItemRow.quantidade}
                          onChange={e => handleQuantityChange(parseFloat(e.target.value))}
                          inputProps={{ min: 0.01, step: 0.01 }}
                          sx={{ width: '100px' }}
                        />

                        {/* Total em tempo real */}
                        <Box sx={{ minWidth: '140px', pt: 1 }}>
                          <Typography variant="body2" color="textSecondary">
                            Total:
                          </Typography>
                          <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                            {newItemRow.calculatedTotal.toLocaleString('pt-BR', {
                              style: 'currency',
                              currency: 'BRL',
                            })}
                          </Typography>
                        </Box>

                        {/* Botões de confirmar/cancelar */}
                        <Stack direction="row" spacing={1}>
                          <IconButton
                            color="success"
                            onClick={handleConfirmNewItem}
                            disabled={
                              !newItemRow.selectedItem ||
                              newItemRow.quantidade <= 0 ||
                              isSubmitting
                            }
                            title="Confirmar"
                          >
                            <CheckIcon />
                          </IconButton>
                          <IconButton
                            color="error"
                            onClick={handleCloseNewItemRow}
                            disabled={isSubmitting}
                            title="Cancelar"
                          >
                            <CloseIcon />
                          </IconButton>
                        </Stack>
                      </Stack>
                    </Stack>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <Alert severity="info" sx={{ mb: 3 }}>
          Nenhum item adicionado ainda. Use os botões abaixo para começar.
        </Alert>
      )}

      {/* Botões flutuantes para adicionar tipos */}
      {!newItemRow.isOpen && (
        <Stack direction="row" spacing={2} sx={{ mb: 3, flexWrap: 'wrap', gap: 1 }}>
          <Typography variant="body2" color="textSecondary" sx={{ width: '100%', mb: 1 }}>
            Adicionar novo item:
          </Typography>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={() => handleOpenNewItemRow('mao_obra')}
            disabled={isSubmitting}
          >
            + Mão de Obra
          </Button>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={() => handleOpenNewItemRow('epi')}
            disabled={isSubmitting}
          >
            + EPI
          </Button>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={() => handleOpenNewItemRow('equipamento')}
            disabled={isSubmitting}
          >
            + Equipamento
          </Button>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={() => handleOpenNewItemRow('ferramenta')}
            disabled={isSubmitting}
          >
            + Ferramenta
          </Button>
        </Stack>
      )}
    </Container>
  );
}
