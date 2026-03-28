import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import {
  Alert,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { useState } from 'react';
import { z } from 'zod';

import { DataTable } from '../../shared/components/DataTable';
import { EmptyState } from '../../shared/components/EmptyState';
import {
  errorMessages,
  successMessages,
  warningMessages,
} from '../../shared/components/FeedbackMessages';
import { PageHeader } from '../../shared/components/PageHeader';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import { servicesApi } from '../../shared/services/api/servicesApi';
import type { ServicoTcpoResponse } from '../../shared/types/contracts/servicos';
import { formatCurrency } from '../../shared/utils/format';
import { useAuth } from '../auth/AuthProvider';

const createServiceSchema = z.object({
  codigo_origem: z.string().min(1, 'Informe o código do serviço.'),
  descricao: z.string().min(3, 'Informe a descrição do serviço.'),
  unidade_medida: z.string().min(1, 'Informe a unidade.'),
  custo_unitario: z.coerce.number().positive('Informe um custo maior que zero.'),
  categoria_id: z.string().optional(),
});

type CreateServiceFormInput = z.input<typeof createServiceSchema>;
type CreateServiceFormOutput = z.output<typeof createServiceSchema>;

export function ServicesPage() {
  const { user, selectedClientId } = useAuth();
  const { showMessage } = useFeedback();
  const queryClient = useQueryClient();
  const [query, setQuery] = useState('');
  const [categoriaId, setCategoriaId] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedService, setSelectedService] = useState<ServicoTcpoResponse | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<CreateServiceFormInput, undefined, CreateServiceFormOutput>({
    resolver: zodResolver(createServiceSchema),
    defaultValues: {
      codigo_origem: '',
      descricao: '',
      unidade_medida: '',
      custo_unitario: 0,
      categoria_id: '',
    },
  });

  const servicesQuery = useQuery({
    queryKey: ['services', selectedClientId, query, categoriaId, page, pageSize, user?.is_admin],
    queryFn: () =>
      servicesApi.list({
        page,
        page_size: pageSize,
        q: query || undefined,
        categoria_id: categoriaId ? Number(categoriaId) : undefined,
        cliente_id: selectedClientId || undefined,
      }),
    enabled: Boolean(user && (selectedClientId || user.is_admin)),
  });

  const compositionQuery = useQuery({
    queryKey: ['services', 'composition', selectedService?.id],
    queryFn: () => servicesApi.getComposicao(selectedService!.id),
    enabled: Boolean(selectedService?.id),
  });

  const createServiceMutation = useMutation({
    mutationFn: (values: CreateServiceFormOutput) =>
      servicesApi.create({
        codigo_origem: values.codigo_origem,
        descricao: values.descricao,
        unidade_medida: values.unidade_medida,
        custo_unitario: values.custo_unitario,
        categoria_id: values.categoria_id ? Number(values.categoria_id) : null,
      }),
    onSuccess: () => {
      showMessage(successMessages.serviceCreated);
      setCreateDialogOpen(false);
      reset();
      void queryClient.invalidateQueries({ queryKey: ['services'] });
    },
  });

  if (!selectedClientId && !user?.is_admin) {
    return (
      <>
        <PageHeader
          title="Catálogo de Serviços"
          description="Consulte os serviços disponíveis para orçamentação no contexto do cliente atual."
        />
        <EmptyState
          title="Selecione um cliente para listar o catálogo"
          description="Defina o cliente no topo para carregar os serviços visíveis e abrir o detalhamento das composições."
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Catálogo de Serviços"
        description="Gerencie os serviços do catálogo com filtros, detalhamento de composição e criação administrativa quando disponível."
        actions={
          user?.is_admin ? (
            <Button
              variant="contained"
              startIcon={<AddOutlinedIcon />}
              onClick={() => setCreateDialogOpen(true)}
            >
              Novo serviço
            </Button>
          ) : undefined
        }
      />

      <Stack direction={{ xs: 'column', xl: 'row' }} spacing={2}>
        <Paper sx={{ flex: 1.2, p: 3, border: '1px solid', borderColor: 'divider' }}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 2 }}>
            <TextField
              fullWidth
              label="Buscar"
              placeholder="Buscar..."
              value={query}
              onChange={(event) => {
                setQuery(event.target.value);
                setPage(1);
              }}
            />
            <TextField
              label="Categoria"
              value={categoriaId}
              onChange={(event) => {
                setCategoriaId(event.target.value);
                setPage(1);
              }}
            />
          </Stack>

          {servicesQuery.isError ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              {extractApiErrorMessage(servicesQuery.error, errorMessages.loadData)}
            </Alert>
          ) : null}

          <DataTable
            columns={[
              { key: 'codigo', header: 'Código', render: (row) => row.codigo_origem },
              { key: 'descricao', header: 'Descrição', render: (row) => row.descricao },
              { key: 'unidade', header: 'Unidade', render: (row) => row.unidade_medida },
              {
                key: 'origem',
                header: 'Origem',
                render: (row) => <StatusBadge value={row.origem} />,
              },
              {
                key: 'custo',
                header: 'Custo unitário (R$)',
                align: 'right',
                render: (row) => formatCurrency(row.custo_unitario),
              },
            ]}
            rows={servicesQuery.data?.items ?? []}
            rowKey={(row) => row.id}
            loading={servicesQuery.isLoading}
            page={page}
            pageSize={pageSize}
            total={servicesQuery.data?.total ?? 0}
            emptyTitle="Seu catálogo está vazio"
            emptyDescription="Nenhum serviço disponível para o recorte atual. Ajuste os filtros ou cadastre novos itens."
            onPageChange={setPage}
            onPageSizeChange={(value) => {
              setPageSize(value);
              setPage(1);
            }}
            onRowClick={(row) => setSelectedService(row)}
          />
        </Paper>

        <Paper sx={{ flex: 0.8, p: 3, border: '1px solid', borderColor: 'divider' }}>
          <Typography variant="h6" sx={{ mb: 1.5 }}>
            Detalhes do serviço
          </Typography>
          {selectedService ? (
            <Stack spacing={1.5}>
              <Typography variant="subtitle1">{selectedService.descricao}</Typography>
              <Typography variant="body2" color="text.secondary">
                Código: {selectedService.codigo_origem}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Unidade: {selectedService.unidade_medida}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Custo unitário: {formatCurrency(selectedService.custo_unitario)}
              </Typography>
              <Stack direction="row" spacing={1}>
                <StatusBadge value={selectedService.origem} />
              </Stack>

              {compositionQuery.isFetching ? (
                <Typography variant="body2" color="text.secondary">
                  Carregando composições...
                </Typography>
              ) : compositionQuery.data ? (
                <>
                  <Typography variant="subtitle2">Composição</Typography>
                  {compositionQuery.data.itens.length ? (
                    compositionQuery.data.itens.map((item) => (
                      <Paper key={item.id} variant="outlined" sx={{ p: 1.5 }}>
                        <Typography variant="body2">{item.descricao_filho}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {item.quantidade_consumo} {item.unidade_medida} ·{' '}
                          {formatCurrency(item.custo_total)}
                        </Typography>
                      </Paper>
                    ))
                  ) : (
                    <Alert severity="warning">{warningMessages.serviceNoComposition}</Alert>
                  )}
                </>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Selecione um serviço para abrir o detalhamento.
                </Typography>
              )}
            </Stack>
          ) : (
            <EmptyState
              title="Nenhum serviço selecionado"
              description="Selecione um serviço na tabela para revisar dados, origem e composição."
            />
          )}
        </Paper>
      </Stack>

      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Novo serviço</DialogTitle>
        <DialogContent dividers>
          <Stack
            component="form"
            spacing={2}
            sx={{ mt: 0.5 }}
            onSubmit={handleSubmit((values) => createServiceMutation.mutate(values))}
          >
            <TextField
              label="Código"
              error={Boolean(errors.codigo_origem)}
              helperText={errors.codigo_origem?.message}
              {...register('codigo_origem')}
            />
            <TextField
              label="Descrição"
              multiline
              minRows={3}
              error={Boolean(errors.descricao)}
              helperText={errors.descricao?.message}
              {...register('descricao')}
            />
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <TextField
                label="Unidade"
                error={Boolean(errors.unidade_medida)}
                helperText={errors.unidade_medida?.message}
                {...register('unidade_medida')}
              />
              <TextField
                label="Custo unitário"
                type="number"
                error={Boolean(errors.custo_unitario)}
                helperText={errors.custo_unitario?.message}
                {...register('custo_unitario', { valueAsNumber: true })}
              />
            </Stack>
            <TextField
              label="Categoria"
              error={Boolean(errors.categoria_id)}
              helperText={errors.categoria_id?.message}
              {...register('categoria_id')}
            />
            {createServiceMutation.isError ? (
              <Alert severity="error">
                {extractApiErrorMessage(createServiceMutation.error, errorMessages.serviceSave)}
              </Alert>
            ) : null}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={handleSubmit((values) => createServiceMutation.mutate(values))}
            disabled={createServiceMutation.isPending}
          >
            {createServiceMutation.isPending ? (
              <CircularProgress size={20} color="inherit" />
            ) : (
              'Salvar'
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
