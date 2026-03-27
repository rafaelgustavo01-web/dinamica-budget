import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import ToggleOffOutlinedIcon from '@mui/icons-material/ToggleOffOutlined';
import ToggleOnOutlinedIcon from '@mui/icons-material/ToggleOnOutlined';
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

import { ConfirmationDialog } from '../../shared/components/ConfirmationDialog';
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

const editClientSchema = z.object({
  nome_fantasia: z.string().min(2, 'Informe ao menos 2 caracteres.'),
});

type CreateClientFormInput = z.input<typeof createClientSchema>;
type CreateClientFormOutput = z.output<typeof createClientSchema>;
type EditClientFormValues = z.infer<typeof editClientSchema>;
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
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [confirmStatusOpen, setConfirmStatusOpen] = useState(false);

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

  const {
    register: registerEdit,
    handleSubmit: handleEditSubmit,
    formState: { errors: editErrors },
    reset: resetEditForm,
  } = useForm<EditClientFormValues>({
    resolver: zodResolver(editClientSchema),
    defaultValues: {
      nome_fantasia: '',
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

  const updateClientMutation = useMutation({
    mutationFn: (values: EditClientFormValues) =>
      clientsApi.patch(selectedClient!.id, values),
    onSuccess: (data) => {
      showMessage('Cliente atualizado com sucesso.');
      setSelectedClientId(data.id);
      setEditDialogOpen(false);
      void queryClient.invalidateQueries({ queryKey: ['clients'] });
    },
  });

  const toggleStatusMutation = useMutation({
    mutationFn: () =>
      clientsApi.patch(selectedClient!.id, {
        is_active: !selectedClient!.is_active,
      }),
    onSuccess: (data) => {
      showMessage(
        data.is_active ? 'Cliente reativado com sucesso.' : 'Cliente inativado com sucesso.',
      );
      setSelectedClientId(data.id);
      setConfirmStatusOpen(false);
      void queryClient.invalidateQueries({ queryKey: ['clients'] });
    },
  });

  return (
    <>
      <PageHeader
        title="Clientes"
        description="Listagem administrativa com cadastro, edicao de nome fantasia e ativacao/inativacao consumindo os contratos oficiais publicados pelo backend."
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
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
                <Button
                  variant="outlined"
                  startIcon={<EditOutlinedIcon />}
                  onClick={() => {
                    resetEditForm({ nome_fantasia: selectedClient.nome_fantasia });
                    setEditDialogOpen(true);
                  }}
                >
                  Editar nome
                </Button>
                <Button
                  variant="outlined"
                  color={selectedClient.is_active ? 'warning' : 'success'}
                  startIcon={
                    selectedClient.is_active ? (
                      <ToggleOffOutlinedIcon />
                    ) : (
                      <ToggleOnOutlinedIcon />
                    )
                  }
                  onClick={() => setConfirmStatusOpen(true)}
                >
                  {selectedClient.is_active ? 'Inativar' : 'Reativar'}
                </Button>
              </Stack>
              <Alert severity="info" variant="outlined">
                O contrato administrativo atual permite editar o nome fantasia e alterar o
                status do cliente. O CNPJ permanece somente leitura neste fluxo.
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

      <Dialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>Editar cliente</DialogTitle>
        <DialogContent dividers>
          <Stack
            component="form"
            spacing={2}
            sx={{ mt: 0.5 }}
            onSubmit={handleEditSubmit((values) => updateClientMutation.mutate(values))}
          >
            <TextField
              label="Nome fantasia"
              error={Boolean(editErrors.nome_fantasia)}
              helperText={editErrors.nome_fantasia?.message}
              {...registerEdit('nome_fantasia')}
            />
            {updateClientMutation.isError ? (
              <Alert severity="error">
                {extractApiErrorMessage(
                  updateClientMutation.error,
                  'Falha ao atualizar o cliente.',
                )}
              </Alert>
            ) : null}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={handleEditSubmit((values) => updateClientMutation.mutate(values))}
            disabled={updateClientMutation.isPending}
          >
            {updateClientMutation.isPending ? (
              <CircularProgress size={20} color="inherit" />
            ) : (
              'Salvar'
            )}
          </Button>
        </DialogActions>
      </Dialog>

      <ConfirmationDialog
        open={confirmStatusOpen}
        title={selectedClient?.is_active ? 'Inativar cliente?' : 'Reativar cliente?'}
        confirmLabel={selectedClient?.is_active ? 'Inativar' : 'Reativar'}
        confirmColor={selectedClient?.is_active ? 'error' : 'primary'}
        isLoading={toggleStatusMutation.isPending}
        onCancel={() => setConfirmStatusOpen(false)}
        onConfirm={() => toggleStatusMutation.mutate()}
      >
        <Stack spacing={1}>
          <Typography variant="body2">
            Cliente: {selectedClient?.nome_fantasia}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {selectedClient?.is_active
              ? 'O cliente sera marcado como inativo no backend.'
              : 'O cliente voltara a ficar ativo no backend.'}
          </Typography>
          {toggleStatusMutation.isError ? (
            <Alert severity="error">
              {extractApiErrorMessage(
                toggleStatusMutation.error,
                'Falha ao alterar o status do cliente.',
              )}
            </Alert>
          ) : null}
        </Stack>
      </ConfirmationDialog>
    </>
  );
}
