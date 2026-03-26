import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import {
  Alert,
  Button,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { DataTable } from '../../shared/components/DataTable';
import { EmptyState } from '../../shared/components/EmptyState';
import { PageHeader } from '../../shared/components/PageHeader';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import { clientsApi } from '../../shared/services/api/clientsApi';
import { shortenUuid } from '../../shared/utils/format';

const createClientSchema = z.object({
  nome_fantasia: z.string().min(2, 'Informe ao menos 2 caracteres.'),
  cnpj: z
    .string()
    .transform((value) => value.replace(/\D/g, ''))
    .refine((value) => /^\d{14}$/.test(value), 'Informe 14 digitos numericos.'),
});

type CreateClientFormInput = z.input<typeof createClientSchema>;
type CreateClientFormOutput = z.output<typeof createClientSchema>;
type StatusFilter = 'all' | 'active' | 'inactive';

function getClientStatusLabel(isActive: boolean) {
  return isActive ? 'Ativo' : 'Inativo';
}

export function ClientsPage() {
  const { showMessage } = useFeedback();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedClientId, setSelectedClientId] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<CreateClientFormInput, undefined, CreateClientFormOutput>({
    resolver: zodResolver(createClientSchema),
    defaultValues: {
      nome_fantasia: '',
      cnpj: '',
    },
  });

  const clientsQuery = useQuery({
    queryKey: ['clients', statusFilter, page, pageSize],
    queryFn: () =>
      clientsApi.list({
        page,
        page_size: pageSize,
        is_active:
          statusFilter === 'all' ? undefined : statusFilter === 'active',
      }),
  });
  const clientRows = clientsQuery.data?.items ?? [];
  const selectedClient =
    clientRows.find((item) => item.id === selectedClientId) ?? clientRows[0] ?? null;

  const createClientMutation = useMutation({
    mutationFn: (values: CreateClientFormOutput) => clientsApi.create(values),
    onSuccess: (data) => {
      showMessage('Cliente criado com sucesso.');
      setCreateDialogOpen(false);
      reset();
      setSelectedClientId(data.id);
      void queryClient.invalidateQueries({ queryKey: ['clients'] });
    },
  });

  return (
    <>
      <PageHeader
        title="Clientes"
        description="Listagem administrativa e cadastro real de clientes, consumindo os contratos oficiais publicados pelo backend."
        actions={
          <Button
            variant="contained"
            startIcon={<AddOutlinedIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Novo cliente
          </Button>
        }
      />

      <Stack direction={{ xs: 'column', xl: 'row' }} spacing={2}>
        <Paper sx={{ flex: 1.2, p: 3 }}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 2 }}>
            <TextField
              select
              label="Status"
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value as StatusFilter);
                setPage(1);
              }}
              sx={{ minWidth: 220 }}
            >
              <MenuItem value="all">Todos</MenuItem>
              <MenuItem value="active">Somente ativos</MenuItem>
              <MenuItem value="inactive">Somente inativos</MenuItem>
            </TextField>
          </Stack>

          {clientsQuery.isError ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              {extractApiErrorMessage(
                clientsQuery.error,
                'Falha ao carregar os clientes.',
              )}
            </Alert>
          ) : null}

          <DataTable
            columns={[
              {
                key: 'nome',
                header: 'Nome fantasia',
                render: (row) => row.nome_fantasia,
              },
              {
                key: 'cnpj',
                header: 'CNPJ',
                render: (row) => row.cnpj,
              },
              {
                key: 'status',
                header: 'Status',
                render: (row) => getClientStatusLabel(row.is_active),
              },
            ]}
            rows={clientsQuery.data?.items ?? []}
            rowKey={(row) => row.id}
            loading={clientsQuery.isLoading}
            page={page}
            pageSize={pageSize}
            total={clientsQuery.data?.total ?? 0}
            emptyTitle="Nenhum cliente encontrado"
            emptyDescription="A listagem reflete apenas os filtros oficialmente suportados pelo endpoint administrativo de clientes."
            onPageChange={setPage}
            onPageSizeChange={(value) => {
              setPageSize(value);
              setPage(1);
            }}
            onRowClick={(row) => setSelectedClientId(row.id)}
          />
        </Paper>

        <Paper sx={{ flex: 0.8, p: 3 }}>
          <Typography variant="h6" sx={{ mb: 1.5 }}>
            Detalhes do cliente
          </Typography>

          {selectedClient ? (
            <Stack spacing={1.5}>
              <Typography variant="subtitle1">{selectedClient.nome_fantasia}</Typography>
              <Typography variant="body2" color="text.secondary">
                CNPJ: {selectedClient.cnpj}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Status: {getClientStatusLabel(selectedClient.is_active)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                ID: {shortenUuid(selectedClient.id)}
              </Typography>
              <Alert severity="info" variant="outlined">
                O backend atual ja publica listagem e cadastro. Edicao e ativacao/inativacao continuam dependentes de contratos REST adicionais.
              </Alert>
            </Stack>
          ) : (
            <EmptyState
              title="Nenhum cliente selecionado"
              description="Selecione um cliente na tabela para revisar os dados retornados pelo backend."
            />
          )}
        </Paper>
      </Stack>

      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>Novo cliente</DialogTitle>
        <DialogContent dividers>
          <Stack
            component="form"
            spacing={2}
            sx={{ mt: 0.5 }}
            onSubmit={handleSubmit((values) => createClientMutation.mutate(values))}
          >
            <TextField
              label="Nome fantasia"
              error={Boolean(errors.nome_fantasia)}
              helperText={errors.nome_fantasia?.message}
              {...register('nome_fantasia')}
            />
            <TextField
              label="CNPJ"
              inputProps={{ inputMode: 'numeric', maxLength: 18 }}
              error={Boolean(errors.cnpj)}
              helperText={errors.cnpj?.message ?? 'Use 14 digitos numericos, sem mascara.'}
              {...register('cnpj')}
            />
            {createClientMutation.isError ? (
              <Alert severity="error">
                {extractApiErrorMessage(
                  createClientMutation.error,
                  'Falha ao criar o cliente.',
                )}
              </Alert>
            ) : null}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={handleSubmit((values) => createClientMutation.mutate(values))}
            disabled={createClientMutation.isPending}
          >
            {createClientMutation.isPending ? (
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
