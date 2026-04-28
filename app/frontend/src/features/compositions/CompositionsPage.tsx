import AddIcon from '@mui/icons-material/Add';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  InputAdornment,
  List,
  ListItemButton,
  ListItemText,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { useAuth } from '../auth/AuthProvider';
import { ConfirmationDialog } from '../../shared/components/ConfirmationDialog';
import { EmptyState } from '../../shared/components/EmptyState';
import {
  errorMessages,
  successMessages,
  warningMessages,
} from '../../shared/components/FeedbackMessages';
import { PageHeader } from '../../shared/components/PageHeader';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import { composicoesApi } from '../../shared/services/api/composicoesApi';
import { servicesApi } from '../../shared/services/api/servicesApi';
import type { ServicoTcpoResponse } from '../../shared/types/contracts/servicos';
import { formatCurrency } from '../../shared/utils/format';
import { hasClientePerfil } from '../../shared/utils/permissions';
import { ExpandableTreeRow } from './components/ExpandableTreeRow';

export function CompositionsPage() {
  const { user, selectedClientId } = useAuth();
  const { showMessage } = useFeedback();
  const queryClient = useQueryClient();

  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [selectedService, setSelectedService] = useState<ServicoTcpoResponse | null>(null);

  const [cloneOpen, setCloneOpen] = useState(false);
  const [cloneCode, setCloneCode] = useState('');
  const [cloneDesc, setCloneDesc] = useState('');

  const [addOpen, setAddOpen] = useState(false);
  const [addSearch, setAddSearch] = useState('');
  const [addSearchPage] = useState(1);
  const [selectedComponent, setSelectedComponent] = useState<ServicoTcpoResponse | null>(null);
  const [addQty, setAddQty] = useState('1');
  const [componentToRemove, setComponentToRemove] = useState<{
    id: string;
    descricao: string;
  } | null>(null);

  const canEdit =
    Boolean(selectedClientId) &&
    (user?.is_admin || hasClientePerfil(user, selectedClientId, ['APROVADOR', 'ADMIN']));

  const isOwnedByClient =
    selectedService?.origem === 'PROPRIA' && selectedService?.cliente_id === selectedClientId;

  const servicesQuery = useQuery({
    queryKey: ['composition-page', selectedClientId, query, page, pageSize],
    queryFn: () =>
      servicesApi.list({
        page,
        page_size: pageSize,
        q: query || undefined,
        cliente_id: selectedClientId || undefined,
      }),
    enabled: Boolean(user && (selectedClientId || user.is_admin)),
  });

  const compositionQuery = useQuery({
    queryKey: ['composition-page', 'composition', selectedService?.id],
    queryFn: () => servicesApi.getComposicao(selectedService!.id),
    enabled: Boolean(selectedService?.id),
  });

  const componentSearchQuery = useQuery({
    queryKey: ['composition-page', 'component-search', addSearch, addSearchPage, selectedClientId],
    queryFn: () =>
      servicesApi.list({
        page: addSearchPage,
        page_size: 10,
        q: addSearch || undefined,
        cliente_id: selectedClientId || undefined,
      }),
    enabled: addOpen,
  });

  const cloneMutation = useMutation({
    mutationFn: () =>
      composicoesApi.clonar({
        servico_origem_id: selectedService!.id,
        cliente_id: selectedClientId,
        codigo_clone: cloneCode,
        descricao: cloneDesc || undefined,
      }),
    onSuccess: (data) => {
      showMessage(successMessages.compositionCloned);
      void queryClient.invalidateQueries({ queryKey: ['composition-page'] });
      void queryClient.invalidateQueries({ queryKey: ['services'] });
      setSelectedService(data.servico);
      setCloneOpen(false);
      setCloneCode('');
      setCloneDesc('');
    },
  });

  const addComponentMutation = useMutation({
    mutationFn: () =>
      composicoesApi.adicionarComponente(selectedService!.id, {
        insumo_filho_id: selectedComponent!.id,
        quantidade_consumo: Number(addQty),
        unidade_medida: selectedComponent!.unidade_medida,
      }),
    onSuccess: (data) => {
      showMessage(successMessages.componentAdded);
      setSelectedService(data.servico);
      void queryClient.invalidateQueries({ queryKey: ['composition-page'] });
      void queryClient.invalidateQueries({ queryKey: ['services'] });
      setAddOpen(false);
      setAddSearch('');
      setSelectedComponent(null);
      setAddQty('1');
    },
  });

  const removeComponentMutation = useMutation({
    mutationFn: () => composicoesApi.removerComponente(selectedService!.id, componentToRemove!.id),
    onSuccess: () => {
      showMessage(successMessages.componentRemoved);
      setComponentToRemove(null);
      void queryClient.invalidateQueries({ queryKey: ['composition-page'] });
      void queryClient.invalidateQueries({ queryKey: ['services'] });
    },
  });

  if (!selectedClientId && !user?.is_admin) {
    return (
      <>
        <PageHeader
          title="Composições"
          description="Visualize a estrutura de custos dos serviços e acompanhe a composição disponível para o cliente atual."
        />
        <EmptyState
          title="Selecione um cliente para consultar composições"
          description="Defina o cliente no topo para carregar os serviços disponíveis e abrir a estrutura de custos correspondente."
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Composições"
        description="Visualize composições existentes, clone estruturas para o catálogo próprio e ajuste componentes quando o perfil permitir."
      />

      <Stack direction={{ xs: 'column', xl: 'row' }} spacing={2}>
        <Paper sx={{ flex: 1, p: 3, border: '1px solid', borderColor: 'divider' }}>
          <TextField
            fullWidth
            label="Buscar serviço"
            placeholder="Buscar..."
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(1);
            }}
            sx={{ mb: 2 }}
          />

          {servicesQuery.isError ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              {extractApiErrorMessage(servicesQuery.error, errorMessages.loadData)}
            </Alert>
          ) : null}

          <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 560 }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 700 }}>Descrição</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Código</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Unidade</TableCell>
                  <TableCell sx={{ fontWeight: 700 }} align="right">Custo</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Tipo</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {servicesQuery.isLoading ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                      <Typography variant="body2" color="text.secondary">Carregando...</Typography>
                    </TableCell>
                  </TableRow>
                ) : servicesQuery.data?.items.length ? (
                  servicesQuery.data.items.map((row) => (
                    <ExpandableTreeRow
                      key={row.id}
                      item={{
                        id: row.id,
                        descricao: row.descricao,
                        codigo_origem: row.codigo_origem,
                        unidade_medida: row.unidade_medida,
                        custo_unitario: row.custo_unitario,
                        tipo_recurso: row.tipo_recurso,
                      }}
                      isSelected={selectedService?.id === row.id}
                      onSelect={(id) => {
                        const svc = servicesQuery.data.items.find((r) => r.id === id) ?? null;
                        setSelectedService(svc);
                      }}
                    />
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                      <Typography variant="body2" color="text.secondary">
                        Nenhuma composição cadastrada
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {servicesQuery.data && servicesQuery.data.total > pageSize ? (
            <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mt: 1 }}>
              <Typography variant="caption" color="text.secondary">
                Página {page} de {Math.ceil(servicesQuery.data.total / pageSize)}
              </Typography>
              <Stack direction="row" spacing={1}>
                <Button size="small" variant="outlined" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                  Anterior
                </Button>
                <Button
                  size="small"
                  variant="outlined"
                  disabled={page * pageSize >= servicesQuery.data.total}
                  onClick={() => setPage(page + 1)}
                >
                  Próxima
                </Button>
              </Stack>
            </Stack>
          ) : null}
        </Paper>

        <Paper sx={{ flex: 0.9, p: 3, border: '1px solid', borderColor: 'divider' }}>
          <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1.5 }}>
            <Typography variant="h6">Composição do serviço</Typography>
            {selectedService && canEdit ? (
              <Stack direction="row" spacing={1}>
                <Tooltip title="Clonar composição">
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<ContentCopyIcon />}
                    onClick={() => setCloneOpen(true)}
                  >
                    Clonar composição
                  </Button>
                </Tooltip>
                {isOwnedByClient ? (
                  <Tooltip title="Adicionar componente">
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<AddIcon />}
                      onClick={() => setAddOpen(true)}
                    >
                      Adicionar componente
                    </Button>
                  </Tooltip>
                ) : null}
              </Stack>
            ) : null}
          </Stack>

          {cloneMutation.isError ? (
            <Alert severity="error" sx={{ mb: 1 }}>
              {extractApiErrorMessage(cloneMutation.error, errorMessages.compositionClone)}
            </Alert>
          ) : null}

          {addComponentMutation.isError ? (
            <Alert severity="error" sx={{ mb: 1 }}>
              {extractApiErrorMessage(
                addComponentMutation.error,
                errorMessages.compositionAddComponent,
              )}
            </Alert>
          ) : null}

          {removeComponentMutation.isError ? (
            <Alert severity="error" sx={{ mb: 1 }}>
              {extractApiErrorMessage(
                removeComponentMutation.error,
                errorMessages.compositionRemoveComponent,
              )}
            </Alert>
          ) : null}

          {selectedService ? (
            compositionQuery.data ? (
              <Stack spacing={1.5}>
                <Typography variant="subtitle1">{selectedService.descricao}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Custo total da composição: {formatCurrency(compositionQuery.data.custo_total_composicao)}
                </Typography>
                {compositionQuery.data.itens.length ? (
                  compositionQuery.data.itens.map((item) => (
                    <Paper key={item.id} variant="outlined" sx={{ p: 1.5 }}>
                      <Stack direction="row" alignItems="flex-start" justifyContent="space-between">
                        <Stack spacing={0.25}>
                          <Typography variant="body2">{item.descricao_filho}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {item.quantidade_consumo} {item.unidade_medida} ·{' '}
                            {formatCurrency(item.custo_total)}
                          </Typography>
                        </Stack>
                        {isOwnedByClient && canEdit ? (
                          <Tooltip title="Remover componente">
                            <IconButton
                              size="small"
                              onClick={() =>
                                setComponentToRemove({
                                  id: item.id,
                                  descricao: item.descricao_filho,
                                })
                              }
                              disabled={removeComponentMutation.isPending}
                            >
                              <DeleteOutlineIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        ) : null}
                      </Stack>
                    </Paper>
                  ))
                ) : (
                  <Alert severity="warning">{warningMessages.serviceNoComposition}</Alert>
                )}
              </Stack>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Selecione um serviço para carregar a composição.
              </Typography>
            )
          ) : (
            <EmptyState
              title="Nenhuma composição selecionada"
              description="Escolha um serviço na lista para visualizar os componentes e o custo agregado."
            />
          )}
        </Paper>
      </Stack>

      <Dialog open={cloneOpen} onClose={() => setCloneOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Clonar composição</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Código do clone"
              value={cloneCode}
              onChange={(event) => setCloneCode(event.target.value)}
              required
              fullWidth
              helperText="Código único para identificar o novo serviço no catálogo próprio."
            />
            <TextField
              label="Descrição"
              value={cloneDesc}
              onChange={(event) => setCloneDesc(event.target.value)}
              fullWidth
              helperText="Opcional. Se vazio, a descrição original será mantida."
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCloneOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            disabled={!cloneCode.trim() || cloneMutation.isPending}
            onClick={() => cloneMutation.mutate()}
          >
            Clonar composição
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={addOpen} onClose={() => setAddOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Adicionar componente</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Buscar componente"
              value={addSearch}
              onChange={(event) => setAddSearch(event.target.value)}
              fullWidth
              InputProps={{
                endAdornment: componentSearchQuery.isLoading ? (
                  <InputAdornment position="end">...</InputAdornment>
                ) : null,
              }}
            />
            {componentSearchQuery.data?.items.length ? (
              <Paper variant="outlined" sx={{ maxHeight: 220, overflow: 'auto' }}>
                <List dense disablePadding>
                  {componentSearchQuery.data.items.map((service) => (
                    <ListItemButton
                      key={service.id}
                      selected={selectedComponent?.id === service.id}
                      onClick={() => setSelectedComponent(service)}
                    >
                      <ListItemText
                        primary={service.descricao}
                        secondary={`${service.codigo_origem} · ${service.unidade_medida} · ${formatCurrency(service.custo_unitario)}`}
                      />
                    </ListItemButton>
                  ))}
                </List>
              </Paper>
            ) : null}
            <TextField
              label="Quantidade de consumo"
              type="number"
              value={addQty}
              onChange={(event) => setAddQty(event.target.value)}
              fullWidth
              inputProps={{ min: 0.0001, step: 'any' }}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            disabled={!selectedComponent || !addQty || Number(addQty) <= 0 || addComponentMutation.isPending}
            onClick={() => addComponentMutation.mutate()}
          >
            Adicionar componente
          </Button>
        </DialogActions>
      </Dialog>

      <ConfirmationDialog
        open={Boolean(componentToRemove)}
        title="Remover componente"
        confirmLabel="Remover"
        confirmColor="error"
        isLoading={removeComponentMutation.isPending}
        onCancel={() => setComponentToRemove(null)}
        onConfirm={() => removeComponentMutation.mutate()}
      >
        <Typography variant="body2" color="text.secondary">
          {componentToRemove
            ? `Tem certeza de que deseja remover "${componentToRemove.descricao}" desta composição?`
            : 'Confirme a remoção do componente selecionado.'}
        </Typography>
      </ConfirmationDialog>
    </>
  );
}
