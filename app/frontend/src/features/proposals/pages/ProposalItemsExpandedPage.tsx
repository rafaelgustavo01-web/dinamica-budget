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
  Divider,
  Tabs,
  Tab,
  InputAdornment,
} from '@mui/material';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import AddIcon from '@mui/icons-material/Add';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import RefreshIcon from '@mui/icons-material/Refresh';
import SearchIcon from '@mui/icons-material/Search';

import { PageHeader } from '../../../shared/components/PageHeader';
import { proposalsApi } from '../../../shared/services/api/proposalsApi';
import type {
  BcuItem,
  AddBcuItemRequest,
} from '../../../shared/services/api/proposalItemsApi';
import { proposalItemsApi } from '../../../shared/services/api/proposalItemsApi';

type BcuType = 'mao_obra' | 'epi' | 'equipamento' | 'ferramenta';

const BCU_TABS: { value: BcuType; label: string }[] = [
  { value: 'mao_obra', label: 'Mão de Obra' },
  { value: 'epi', label: 'EPI' },
  { value: 'equipamento', label: 'Equipamento' },
  { value: 'ferramenta', label: 'Ferramenta' },
];

const fmtBRL = (v: number) =>
  v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

export function ProposalItemsExpandedPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<BcuType>('mao_obra');
  const [searchFilter, setSearchFilter] = useState('');
  const [quantities, setQuantities] = useState<Record<string, number>>({});

  // ── Queries ────────────────────────────────────────────────────────────────────────

  const { data: proposta, isLoading: isLoadingProposta } = useQuery({
    queryKey: ['proposta', id],
    queryFn: () => proposalsApi.getById(id!),
    enabled: Boolean(id),
  });

  const { data: items = [], isLoading: isLoadingItems, refetch } = useQuery({
    queryKey: ['proposalItems', id],
    queryFn: () => proposalItemsApi.listItems(id!),
    enabled: Boolean(id),
    select: (data) => (Array.isArray(data) ? data : []),
  });

  const {
    data: maoObraItems = [],
    isLoading: isLoadingMaoObra,
    isError: isErrorMaoObra,
    refetch: refetchMaoObra,
  } = useQuery({
    queryKey: ['bcu.mao_obra', id],
    queryFn: () => proposalItemsApi.listMaoObra(id!),
    enabled: Boolean(id),
    select: (data) => (Array.isArray(data) ? data : []),
  });

  const {
    data: epiItems = [],
    isLoading: isLoadingEpi,
    isError: isErrorEpi,
    refetch: refetchEpi,
  } = useQuery({
    queryKey: ['bcu.epi', id],
    queryFn: () => proposalItemsApi.listEpi(id!),
    enabled: Boolean(id),
    select: (data) => (Array.isArray(data) ? data : []),
  });

  const {
    data: equipamentoItems = [],
    isLoading: isLoadingEquipamento,
    isError: isErrorEquipamento,
    refetch: refetchEquipamento,
  } = useQuery({
    queryKey: ['bcu.equipamento', id],
    queryFn: () => proposalItemsApi.listEquipamento(id!),
    enabled: Boolean(id),
    select: (data) => (Array.isArray(data) ? data : []),
  });

  const {
    data: ferramentaItems = [],
    isLoading: isLoadingFerramenta,
    isError: isErrorFerramenta,
    refetch: refetchFerramenta,
  } = useQuery({
    queryKey: ['bcu.ferramenta', id],
    queryFn: () => proposalItemsApi.listFerramenta(id!),
    enabled: Boolean(id),
    select: (data) => (Array.isArray(data) ? data : []),
  });

  // ── Mutations ────────────────────────────────────────────────────────────────────────

  const invalidate = () => {
    refetch();
    queryClient.invalidateQueries({ queryKey: ['proposta', id] });
  };

  const addMaoObraMutation = useMutation({
    mutationFn: (body: AddBcuItemRequest) => proposalItemsApi.addMaoObra(id!, body),
    onSuccess: invalidate,
  });
  const addEpiMutation = useMutation({
    mutationFn: (body: AddBcuItemRequest) => proposalItemsApi.addEpi(id!, body),
    onSuccess: invalidate,
  });
  const addEquipamentoMutation = useMutation({
    mutationFn: (body: AddBcuItemRequest) => proposalItemsApi.addEquipamento(id!, body),
    onSuccess: invalidate,
  });
  const addFerramentaMutation = useMutation({
    mutationFn: (body: AddBcuItemRequest) => proposalItemsApi.addFerramenta(id!, body),
    onSuccess: invalidate,
  });
  const deleteItemMutation = useMutation({
    mutationFn: (itemId: string) => proposalItemsApi.deleteItem(id!, itemId),
    onSuccess: () => refetch(),
  });

  // ── Helpers ────────────────────────────────────────────────────────────────────────

  const getBcuItems = (tipo: BcuType): BcuItem[] => {
    switch (tipo) {
      case 'mao_obra':    return maoObraItems;
      case 'epi':         return epiItems;
      case 'equipamento': return equipamentoItems;
      case 'ferramenta':  return ferramentaItems;
    }
  };

  const isBcuLoading = (): boolean => {
    switch (activeTab) {
      case 'mao_obra':    return isLoadingMaoObra;
      case 'epi':         return isLoadingEpi;
      case 'equipamento': return isLoadingEquipamento;
      case 'ferramenta':  return isLoadingFerramenta;
    }
  };

  const isBcuError = (): boolean => {
    switch (activeTab) {
      case 'mao_obra':    return isErrorMaoObra;
      case 'epi':         return isErrorEpi;
      case 'equipamento': return isErrorEquipamento;
      case 'ferramenta':  return isErrorFerramenta;
    }
  };

  const refetchBcu = () => {
    switch (activeTab) {
      case 'mao_obra':    void refetchMaoObra(); break;
      case 'epi':         void refetchEpi(); break;
      case 'equipamento': void refetchEquipamento(); break;
      case 'ferramenta':  void refetchFerramenta(); break;
    }
  };

  const filteredBcuItems = useMemo(() => {
    const all = getBcuItems(activeTab);
    if (!searchFilter.trim()) return all;
    const q = searchFilter.toLowerCase();
    return all.filter(
      item =>
        item.codigo?.toLowerCase().includes(q) ||
        item.descricao?.toLowerCase().includes(q),
    );
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, searchFilter, maoObraItems, epiItems, equipamentoItems, ferramentaItems]);

  const getQty = (itemId: string) => quantities[itemId] ?? 1;

  const [addError, setAddError] = useState<string | null>(null);

  const handleAdd = async (item: BcuItem) => {
    setAddError(null);
    const payload: AddBcuItemRequest = {
      bcu_item_id: item.id,
      quantidade: getQty(item.id),
    };
    try {
      if (activeTab === 'mao_obra')         await addMaoObraMutation.mutateAsync(payload);
      else if (activeTab === 'epi')         await addEpiMutation.mutateAsync(payload);
      else if (activeTab === 'equipamento') await addEquipamentoMutation.mutateAsync(payload);
      else                                  await addFerramentaMutation.mutateAsync(payload);
      setQuantities(prev => { const n = { ...prev }; delete n[item.id]; return n; });
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      if (detail) setAddError(detail);
      else setAddError('Erro ao adicionar item. Tente novamente.');
    }
  };

  const isAnyPending =
    addMaoObraMutation.isPending ||
    addEpiMutation.isPending ||
    addEquipamentoMutation.isPending ||
    addFerramentaMutation.isPending ||
    deleteItemMutation.isPending;

  const totalValue = items.reduce((acc, item) => acc + (item.valor_total ?? 0), 0);

  // ── Render ────────────────────────────────────────────────────────────────────────
  if (isLoadingProposta || isLoadingItems) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', pt: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!proposta) {
    return <Alert severity="error">Proposta não encontrada</Alert>;
  }

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <PageHeader
        title={`Gerenciar Items — ${proposta.codigo}`}
        description={proposta.titulo || 'Sem título'}
      />

      {/* Barra de ações */}
      <Stack direction="row" spacing={1.5} sx={{ mb: 3 }}>
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

      {/* Card de resumo */}
      <Card
        elevation={0}
        sx={{ mb: 3, border: '1px solid', borderColor: 'divider', borderRadius: 2 }}
      >
        <CardContent sx={{ py: 2, '&:last-child': { pb: 2 } }}>
          <Stack direction="row" spacing={4} alignItems="center">
            <Box>
              <Typography variant="caption" color="text.secondary">
                Status
              </Typography>
              <Box mt={0.5}>
                <Chip
                  label={proposta.status}
                  size="small"
                  sx={{ bgcolor: 'primary.main', color: 'white', fontWeight: 700 }}
                />
              </Box>
            </Box>

            <Divider orientation="vertical" flexItem />

            <Box>
              <Typography variant="caption" color="text.secondary">
                Itens adicionados
              </Typography>
              <Typography variant="h6" fontWeight={700}>
                {items.length}
              </Typography>
            </Box>

            <Divider orientation="vertical" flexItem />

            <Box>
              <Typography variant="caption" color="text.secondary">
                Valor total da proposta
              </Typography>
              <Typography variant="h6" fontWeight={700} color="primary.main">
                {fmtBRL(totalValue)}
              </Typography>
            </Box>
          </Stack>
        </CardContent>
      </Card>

      {/* ================================================================
          CATÁLOGO BCU
          ================================================================ */}
      <Paper
        elevation={0}
        sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2, mb: 3 }}
      >
        {/* Cabeçalho + Tabs */}
        <Box
          sx={{
            px: 3,
            pt: 2.5,
            borderBottom: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Typography variant="h6" fontWeight={600} sx={{ mb: 1.5 }}>
            Catálogo BCU — Selecione os Itens
          </Typography>
          <Tabs
            value={activeTab}
            onChange={(_, v: BcuType) => {
              setActiveTab(v);
              setSearchFilter('');
            }}
            sx={{
              '& .MuiTab-root': {
                fontWeight: 600,
                textTransform: 'none',
                minHeight: 42,
                fontSize: '0.875rem',
              },
            }}
          >
            {BCU_TABS.map(t => (
              <Tab key={t.value} value={t.value} label={t.label} />
            ))}
          </Tabs>
        </Box>

        {/* Barra de filtro */}
        <Box sx={{ px: 3, py: 2 }}>
          <TextField
            size="small"
            fullWidth
            placeholder="Filtrar por codigo ou descrição..."
            value={searchFilter}
            onChange={e => setSearchFilter(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" sx={{ color: 'text.disabled' }} />
                </InputAdornment>
              ),
            }}
            sx={{ maxWidth: 480 }}
          />
        </Box>
        {addError && (
          <Box sx={{ px: 3, pb: 1 }}>
            <Alert severity="warning" onClose={() => setAddError(null)} sx={{ py: 0.5 }}>
              {addError}
            </Alert>
          </Box>
        )}
        {/* Tabela do catalogo */}
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                {[
                  { label: 'Codigo',         align: 'left'  as const },
                  { label: 'Descrição',       align: 'left'  as const },
                  { label: 'Valor Unitário',  align: 'right' as const },
                  { label: 'Quantidade',      align: 'right' as const },
                  { label: 'Total Previsto',  align: 'right' as const },
                  { label: '',               align: 'center' as const },
                ].map(h => (
                  <TableCell
                    key={h.label}
                    align={h.align}
                    sx={{
                      bgcolor: '#1B2A4A',
                      color: '#fff',
                      fontWeight: 700,
                      fontSize: '0.72rem',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      whiteSpace: 'nowrap',
                      borderBottom: 'none',
                      py: 1.5,
                    }}
                  >
                    {h.label}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {isBcuLoading() ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 5 }}>
                    <CircularProgress size={28} />
                  </TableCell>
                </TableRow>
              ) : isBcuError() ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                    <Stack alignItems="center" spacing={1}>
                      <Typography variant="body2" color="error">
                        Erro ao carregar itens BCU
                      </Typography>
                      <Button size="small" variant="outlined" onClick={refetchBcu}>
                        Tentar novamente
                      </Button>
                    </Stack>
                  </TableCell>
                </TableRow>
              ) : filteredBcuItems.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 5, color: 'text.secondary' }}>
                    {searchFilter
                      ? `Nenhum item encontrado para "${searchFilter}"`
                      : 'Nenhum item disponi­vel nesta categoria na base BCU.'}
                  </TableCell>
                </TableRow>
              ) : (
                filteredBcuItems.map(item => {
                  const qty     = getQty(item.id);
                  const preview = item.valor * qty;
                  return (
                    <TableRow
                      key={item.id}
                      hover
                      sx={{ '&:hover': { bgcolor: '#EDF1F8' } }}
                    >
                      {/* Código */}
                      <TableCell
                        sx={{ fontFamily: 'monospace', fontSize: '0.8rem', whiteSpace: 'nowrap' }}
                      >
                        {item.codigo}
                      </TableCell>

                      {/* Descrição */}
                      <TableCell>
                        <Typography variant="body2" sx={{ maxWidth: 380 }}>
                          {item.descricao}
                        </Typography>
                      </TableCell>

                      {/* Valor unitário */}
                      <TableCell align="right" sx={{ whiteSpace: 'nowrap', fontWeight: 500 }}>
                        {fmtBRL(item.valor)}
                      </TableCell>

                      {/* Quantidade editável */}
                      <TableCell align="right" sx={{ width: 120 }}>
                        <TextField
                          size="small"
                          type="number"
                          value={qty}
                          onChange={e => {
                            const v = parseFloat(e.target.value);
                            if (!isNaN(v) && v > 0) {
                              setQuantities(prev => ({ ...prev, [item.id]: v }));
                            }
                          }}
                          inputProps={{ min: 0.01, step: 0.01, style: { textAlign: 'right' } }}
                          sx={{ width: 90 }}
                        />
                      </TableCell>

                      {/* Total previsto */}
                      <TableCell align="right" sx={{ whiteSpace: 'nowrap' }}>
                        <Typography
                          variant="body2"
                          fontWeight={700}
                          sx={{ color: preview > 0 ? '#1B7A3D' : 'text.secondary' }}
                        >
                          {fmtBRL(preview)}
                        </Typography>
                      </TableCell>

                      {/* Botão adicionar */}
                      <TableCell align="center" sx={{ width: 120 }}>
                        <Button
                          size="small"
                          variant="contained"
                          startIcon={<AddIcon />}
                          onClick={() => handleAdd(item)}
                          disabled={isAnyPending || qty <= 0}
                          sx={{
                            textTransform: 'none',
                            fontWeight: 600,
                            whiteSpace: 'nowrap',
                            minWidth: 100,
                          }}
                        >
                          Adicionar
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* ================================================================
          ITENS DA PROPOSTA
      ================================================================ */}
      <Paper
        elevation={0}
        sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 2 }}
      >
        <Box
          sx={{
            px: 3,
            py: 2,
            borderBottom: '1px solid',
            borderColor: 'divider',
            display: 'flex',
            alignItems: 'center',
            gap: 1,
          }}
        >
          <Typography variant="h6" fontWeight={600}>
            Itens da Proposta
          </Typography>
          <Chip
            label={items.length}
            size="small"
            sx={{ bgcolor: 'primary.main', color: 'white', fontWeight: 700 }}
          />
        </Box>

        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                {[
                  { label: 'Ordem',        align: 'left'   as const },
                  { label: 'Codigo',       align: 'left'   as const },
                  { label: 'Descrição',    align: 'left'   as const },
                  { label: 'Qtd',          align: 'right'  as const },
                  { label: 'Un.',          align: 'left'   as const },
                  { label: 'Valor Unit.',  align: 'right'  as const },
                  { label: 'Valor Total',  align: 'right'  as const },
                  { label: '',             align: 'center' as const },
                ].map(h => (
                  <TableCell
                    key={h.label}
                    align={h.align}
                    sx={{
                      fontWeight: 700,
                      fontSize: '0.72rem',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                      color: 'text.secondary',
                      bgcolor: '#F8F9FA',
                      borderBottom: '2px solid',
                      borderColor: 'divider',
                      py: 1.5,
                    }}
                  >
                    {h.label}
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {items.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center" sx={{ py: 5, color: 'text.secondary' }}>
                    Nenhum item adicionado a proposta ainda. Use o catalogo acima para adicionar.
                  </TableCell>
                </TableRow>
              ) : (
                items.map(item => (
                  <TableRow key={item.id} hover>
                    <TableCell sx={{ color: 'text.secondary' }}>{item.ordem ?? 'â€”'}</TableCell>
                    <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                      {item.codigo}
                    </TableCell>
                    <TableCell>{item.descricao}</TableCell>
                    <TableCell align="right">{item.quantidade.toFixed(2)}</TableCell>
                    <TableCell sx={{ color: 'text.secondary' }}>{item.unidade_medida}</TableCell>
                    <TableCell align="right">
                      {item.valor_unitario != null ? fmtBRL(item.valor_unitario) : '—'}
                    </TableCell>
                    <TableCell align="right">
                      {item.valor_total != null ? (
                        <Typography variant="body2" fontWeight={700} color="primary.main">
                          {fmtBRL(item.valor_total)}
                        </Typography>
                      ) : (
                        'â€”'
                      )}
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => deleteItemMutation.mutate(item.id)}
                        disabled={isAnyPending}
                      >
                        <DeleteOutlineIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Rodape com total */}
        {items.length > 0 && (
          <Box
            sx={{
              px: 3,
              py: 2,
              borderTop: '2px solid',
              borderColor: 'primary.main',
              bgcolor: '#EDF1F8',
              borderRadius: '0 0 8px 8px',
            }}
          >
            <Stack direction="row" justifyContent="flex-end" alignItems="center" spacing={2}>
              <Typography variant="body2" color="text.secondary">
                Valor Total da Proposta:
              </Typography>
              <Typography variant="h6" fontWeight={700} color="primary.main">
                {fmtBRL(totalValue)}
              </Typography>
            </Stack>
          </Box>
        )}
      </Paper>
    </Container>
  );
}

