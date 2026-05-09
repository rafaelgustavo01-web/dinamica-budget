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
  Divider,
  InputAdornment,
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
import {
  errorMessages,
  successMessages,
} from '../../shared/components/FeedbackMessages';
import { HelpTooltip } from '../../shared/components/HelpTooltip';
import { PageHeader } from '../../shared/components/PageHeader';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import { clientsApi } from '../../shared/services/api/clientsApi';
import { formatCep, formatCnpj } from '../../shared/utils/format';

const cnpjTransform = (value: string) => value.replace(/\D/g, '');

const baseCommercialSchema = {
  razao_social: z.string().max(255).optional().or(z.literal('')),
  inscricao_estadual: z.string().max(30).optional().or(z.literal('')),
  contato_nome: z.string().max(255).optional().or(z.literal('')),
  contato_telefone: z.string().max(20).optional().or(z.literal('')),
  contato_email: z.string().email('Informe um e-mail válido.').optional().or(z.literal('')),
  endereco_logradouro: z.string().max(500).optional().or(z.literal('')),
  endereco_municipio: z.string().max(100).optional().or(z.literal('')),
  endereco_uf: z
    .string()
    .length(2, 'Use 2 letras, ex: SP')
    .regex(/^[A-Z]{2}$/, 'Use apenas letras maiúsculas, ex: SP')
    .optional()
    .or(z.literal('')),
  endereco_cep: z
    .string()
    .length(8, 'Informe 8 dígitos numéricos.')
    .regex(/^\d{8}$/, 'Use apenas números.')
    .optional()
    .or(z.literal('')),
};

const createClientSchema = z.object({
  nome_fantasia: z.string().min(2, 'Informe ao menos 2 caracteres.').max(255),
  cnpj: z
    .string()
    .transform(cnpjTransform)
    .refine((value) => /^\d{14}$/.test(value), 'Informe 14 dígitos numéricos.'),
  ...baseCommercialSchema,
});

const editClientSchema = z.object({
  nome_fantasia: z.string().min(2, 'Informe ao menos 2 caracteres.').max(255),
  ...baseCommercialSchema,
});

type CreateClientFormOutput = z.output<typeof createClientSchema>;
type EditClientFormValues = z.infer<typeof editClientSchema>;
type StatusFilter = 'all' | 'active' | 'inactive';

function getClientStatusLabel(isActive: boolean) {
  return isActive ? 'Ativo' : 'Inativo';
}

function emptyToNull(value: string | undefined): string | null {
  return value?.trim() || null;
}

export function ClientsPage() {
  const { showMessage } = useFeedback();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [nomeFilter, setNomeFilter] = useState('');
  const [selectedClientId, setSelectedClientId] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [confirmStatusOpen, setConfirmStatusOpen] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<CreateClientFormOutput>({
    resolver: zodResolver(createClientSchema),
    defaultValues: {
      nome_fantasia: '',
      cnpj: '',
      razao_social: '',
      inscricao_estadual: '',
      contato_nome: '',
      contato_telefone: '',
      contato_email: '',
      endereco_logradouro: '',
      endereco_municipio: '',
      endereco_uf: '',
      endereco_cep: '',
    },
  });

  const {
    register: registerEdit,
    handleSubmit: handleEditSubmit,
    formState: { errors: editErrors },
    reset: resetEditForm,
  } = useForm<EditClientFormValues>({
    resolver: zodResolver(editClientSchema),
  });

  const clientsQuery = useQuery({
    queryKey: ['clients', statusFilter, nomeFilter, page, pageSize],
    queryFn: () =>
      clientsApi.list({
        page,
        page_size: pageSize,
        nome: nomeFilter.trim() || undefined,
        is_active:
          statusFilter === 'all' ? undefined : statusFilter === 'active',
      }),
  });
  const clientRows = clientsQuery.data?.items ?? [];
  const selectedClient =
    clientRows.find((item) => item.id === selectedClientId) ?? clientRows[0] ?? null;

  const createClientMutation = useMutation({
    mutationFn: (values: CreateClientFormOutput) =>
      clientsApi.create({
        nome_fantasia: values.nome_fantasia,
        cnpj: values.cnpj,
        razao_social: emptyToNull(values.razao_social),
        inscricao_estadual: emptyToNull(values.inscricao_estadual),
        contato_nome: emptyToNull(values.contato_nome),
        contato_telefone: emptyToNull(values.contato_telefone),
        contato_email: emptyToNull(values.contato_email),
        endereco_logradouro: emptyToNull(values.endereco_logradouro),
        endereco_municipio: emptyToNull(values.endereco_municipio),
        endereco_uf: emptyToNull(values.endereco_uf),
        endereco_cep: emptyToNull(values.endereco_cep),
      }),
    onSuccess: (data) => {
      showMessage(successMessages.clientCreated);
      setCreateDialogOpen(false);
      reset();
      setSelectedClientId(data.id);
      void queryClient.invalidateQueries({ queryKey: ['clients'] });
    },
  });

  const updateClientMutation = useMutation({
    mutationFn: (values: EditClientFormValues) =>
      clientsApi.patch(selectedClient!.id, {
        nome_fantasia: values.nome_fantasia,
        razao_social: emptyToNull(values.razao_social),
        inscricao_estadual: emptyToNull(values.inscricao_estadual),
        contato_nome: emptyToNull(values.contato_nome),
        contato_telefone: emptyToNull(values.contato_telefone),
        contato_email: emptyToNull(values.contato_email),
        endereco_logradouro: emptyToNull(values.endereco_logradouro),
        endereco_municipio: emptyToNull(values.endereco_municipio),
        endereco_uf: emptyToNull(values.endereco_uf),
        endereco_cep: emptyToNull(values.endereco_cep),
      }),
    onSuccess: (data) => {
      showMessage(successMessages.clientUpdated);
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
      showMessage(data.is_active ? successMessages.clientActivated : successMessages.clientDeactivated);
      setSelectedClientId(data.id);
      setConfirmStatusOpen(false);
      void queryClient.invalidateQueries({ queryKey: ['clients'] });
    },
  });

  function openEditDialog() {
    if (!selectedClient) return;
    resetEditForm({
      nome_fantasia: selectedClient.nome_fantasia,
      razao_social: selectedClient.razao_social ?? '',
      inscricao_estadual: selectedClient.inscricao_estadual ?? '',
      contato_nome: selectedClient.contato_nome ?? '',
      contato_telefone: selectedClient.contato_telefone ?? '',
      contato_email: selectedClient.contato_email ?? '',
      endereco_logradouro: selectedClient.endereco_logradouro ?? '',
      endereco_municipio: selectedClient.endereco_municipio ?? '',
      endereco_uf: selectedClient.endereco_uf ?? '',
      endereco_cep: selectedClient.endereco_cep ?? '',
    });
    setEditDialogOpen(true);
  }

  return (
    <>
      <PageHeader
        title="Clientes"
        description="Gerencie os clientes do sistema. Cada cliente possui seu ambiente isolado de dados e usuários vinculados."
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
              label="Buscar por nome"
              placeholder="Filtrar clientes..."
              value={nomeFilter}
              onChange={(event) => {
                setNomeFilter(event.target.value);
                setPage(1);
              }}
              sx={{ flex: 1 }}
            />
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
                render: (row) => formatCnpj(row.cnpj),
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
            emptyTitle="Nenhum cliente cadastrado"
            emptyDescription="Comece cadastrando o primeiro cliente para habilitar o ambiente multi-tenant."
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
            <Stack spacing={2}>
              <Stack spacing={1}>
                <Typography variant="subtitle1" fontWeight={600}>
                  {selectedClient.nome_fantasia}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Razão social: {selectedClient.razao_social || '—'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  CNPJ: {formatCnpj(selectedClient.cnpj)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Inscrição estadual: {selectedClient.inscricao_estadual || '—'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Status: {getClientStatusLabel(selectedClient.is_active)}
                </Typography>
              </Stack>

              <Divider />

              <Stack spacing={0.5}>
                <Typography variant="body2" fontWeight={500} color="text.primary">
                  Contato
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Nome: {selectedClient.contato_nome || '—'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Telefone: {selectedClient.contato_telefone || '—'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  E-mail: {selectedClient.contato_email || '—'}
                </Typography>
              </Stack>

              <Divider />

              <Stack spacing={0.5}>
                <Typography variant="body2" fontWeight={500} color="text.primary">
                  Endereço
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {selectedClient.endereco_logradouro || '—'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {selectedClient.endereco_municipio || '—'}
                  {selectedClient.endereco_municipio && selectedClient.endereco_uf ? ` / ${selectedClient.endereco_uf}` : selectedClient.endereco_uf ? selectedClient.endereco_uf : ''}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  CEP: {formatCep(selectedClient.endereco_cep)}
                </Typography>
              </Stack>

              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
                <Button
                  variant="outlined"
                  startIcon={<EditOutlinedIcon />}
                  onClick={openEditDialog}
                >
                  Editar cliente
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
                O CNPJ permanece somente leitura neste fluxo administrativo.
              </Alert>
            </Stack>
          ) : (
            <EmptyState
              title="Nenhum cliente selecionado"
              description="Selecione um cliente na tabela para revisar dados cadastrais e status."
            />
          )}
        </Paper>
      </Stack>

      {/* Create dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        fullWidth
        maxWidth="md"
      >
        <DialogTitle>Novo cliente</DialogTitle>
        <DialogContent dividers>
          <Stack
            component="form"
            spacing={2}
            sx={{ mt: 0.5 }}
            onSubmit={handleSubmit((values) => createClientMutation.mutate(values))}
          >
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <TextField
                label="Nome fantasia"
                placeholder="Nome comercial do cliente"
                error={Boolean(errors.nome_fantasia)}
                helperText={errors.nome_fantasia?.message ?? 'Nome como aparece na Proposta Comercial.'}
                {...register('nome_fantasia')}
                sx={{ flex: 1 }}
              />
              <TextField
                label="Razão social"
                placeholder="Razão social completa"
                error={Boolean(errors.razao_social)}
                helperText={errors.razao_social?.message}
                {...register('razao_social')}
                sx={{ flex: 1 }}
              />
            </Stack>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <TextField
                label="CNPJ"
                placeholder="00.000.000/0000-00"
                inputProps={{ inputMode: 'numeric', maxLength: 18 }}
                error={Boolean(errors.cnpj)}
                helperText={errors.cnpj?.message ?? 'Use 14 dígitos numéricos, sem máscara.'}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <HelpTooltip title="CNPJ é único no sistema e não pode ser alterado após o cadastro." />
                    </InputAdornment>
                  ),
                }}
                {...register('cnpj')}
                sx={{ flex: 1 }}
              />
              <TextField
                label="Inscrição estadual"
                placeholder="Inscrição estadual"
                error={Boolean(errors.inscricao_estadual)}
                helperText={errors.inscricao_estadual?.message}
                {...register('inscricao_estadual')}
                sx={{ flex: 1 }}
              />
            </Stack>

            <Divider sx={{ my: 1 }} />
            <Typography variant="subtitle2" color="text.secondary">
              Contato
            </Typography>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <TextField
                label="Nome do contato"
                placeholder="Responsável comercial"
                error={Boolean(errors.contato_nome)}
                helperText={errors.contato_nome?.message ?? 'Pessoa de referência para a proposta.'}
                {...register('contato_nome')}
                sx={{ flex: 1 }}
              />
              <TextField
                label="Telefone"
                placeholder="(00) 00000-0000"
                error={Boolean(errors.contato_telefone)}
                helperText={errors.contato_telefone?.message}
                {...register('contato_telefone')}
                sx={{ flex: 1 }}
              />
            </Stack>

            <TextField
              label="E-mail comercial"
              placeholder="email@empresa.com.br"
              error={Boolean(errors.contato_email)}
              helperText={errors.contato_email?.message}
              {...register('contato_email')}
            />

            <Divider sx={{ my: 1 }} />
            <Typography variant="subtitle2" color="text.secondary">
              Endereço
            </Typography>

            <TextField
              label="Logradouro"
              placeholder="Rua, número, complemento"
              error={Boolean(errors.endereco_logradouro)}
              helperText={errors.endereco_logradouro?.message}
              {...register('endereco_logradouro')}
            />

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <TextField
                label="Cidade"
                placeholder="Cidade"
                error={Boolean(errors.endereco_municipio)}
                helperText={errors.endereco_municipio?.message}
                {...register('endereco_municipio')}
                sx={{ flex: 1 }}
              />
              <TextField
                label="UF"
                placeholder="SP"
                inputProps={{
                  maxLength: 2,
                  onInput: (e) => {
                    const el = e.target as HTMLInputElement;
                    el.value = el.value.toUpperCase();
                  },
                }}
                error={Boolean(errors.endereco_uf)}
                helperText={errors.endereco_uf?.message ?? 'Sigla com 2 letras maiúsculas.'}
                {...register('endereco_uf')}
                sx={{ minWidth: 120 }}
              />
              <TextField
                label="CEP"
                placeholder="00000000"
                inputProps={{ inputMode: 'numeric', maxLength: 8 }}
                error={Boolean(errors.endereco_cep)}
                helperText={errors.endereco_cep?.message ?? '8 dígitos numéricos, sem traço.'}
                {...register('endereco_cep')}
                sx={{ minWidth: 160 }}
              />
            </Stack>

            {createClientMutation.isError ? (
              <Alert severity="error">
                {extractApiErrorMessage(
                  createClientMutation.error,
                  errorMessages.clientCreate,
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

      {/* Edit dialog */}
      <Dialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        fullWidth
        maxWidth="md"
      >
        <DialogTitle>Editar cliente</DialogTitle>
        <DialogContent dividers>
          <Stack
            component="form"
            spacing={2}
            sx={{ mt: 0.5 }}
            onSubmit={handleEditSubmit((values) => updateClientMutation.mutate(values))}
          >
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <TextField
                label="Nome fantasia"
                placeholder="Nome comercial do cliente"
                error={Boolean(editErrors.nome_fantasia)}
                helperText={editErrors.nome_fantasia?.message ?? 'Nome como aparece na Proposta Comercial.'}
                {...registerEdit('nome_fantasia')}
                sx={{ flex: 1 }}
              />
              <TextField
                label="Razão social"
                placeholder="Razão social completa"
                error={Boolean(editErrors.razao_social)}
                helperText={editErrors.razao_social?.message}
                {...registerEdit('razao_social')}
                sx={{ flex: 1 }}
              />
            </Stack>

            <TextField
              label="Inscrição estadual"
              placeholder="Inscrição estadual"
              error={Boolean(editErrors.inscricao_estadual)}
              helperText={editErrors.inscricao_estadual?.message}
              {...registerEdit('inscricao_estadual')}
            />

            <Divider sx={{ my: 1 }} />
            <Typography variant="subtitle2" color="text.secondary">
              Contato
            </Typography>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <TextField
                label="Nome do contato"
                placeholder="Responsável comercial"
                error={Boolean(editErrors.contato_nome)}
                helperText={editErrors.contato_nome?.message ?? 'Pessoa de referência para a proposta.'}
                {...registerEdit('contato_nome')}
                sx={{ flex: 1 }}
              />
              <TextField
                label="Telefone"
                placeholder="(00) 00000-0000"
                error={Boolean(editErrors.contato_telefone)}
                helperText={editErrors.contato_telefone?.message}
                {...registerEdit('contato_telefone')}
                sx={{ flex: 1 }}
              />
            </Stack>

            <TextField
              label="E-mail comercial"
              placeholder="email@empresa.com.br"
              error={Boolean(editErrors.contato_email)}
              helperText={editErrors.contato_email?.message}
              {...registerEdit('contato_email')}
            />

            <Divider sx={{ my: 1 }} />
            <Typography variant="subtitle2" color="text.secondary">
              Endereço
            </Typography>

            <TextField
              label="Logradouro"
              placeholder="Rua, número, complemento"
              error={Boolean(editErrors.endereco_logradouro)}
              helperText={editErrors.endereco_logradouro?.message}
              {...registerEdit('endereco_logradouro')}
            />

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <TextField
                label="Cidade"
                placeholder="Cidade"
                error={Boolean(editErrors.endereco_municipio)}
                helperText={editErrors.endereco_municipio?.message}
                {...registerEdit('endereco_municipio')}
                sx={{ flex: 1 }}
              />
              <TextField
                label="UF"
                placeholder="SP"
                inputProps={{
                  maxLength: 2,
                  onInput: (e) => {
                    const el = e.target as HTMLInputElement;
                    el.value = el.value.toUpperCase();
                  },
                }}
                error={Boolean(editErrors.endereco_uf)}
                helperText={editErrors.endereco_uf?.message ?? 'Sigla com 2 letras maiúsculas.'}
                {...registerEdit('endereco_uf')}
                sx={{ minWidth: 120 }}
              />
              <TextField
                label="CEP"
                placeholder="00000000"
                inputProps={{ inputMode: 'numeric', maxLength: 8 }}
                error={Boolean(editErrors.endereco_cep)}
                helperText={editErrors.endereco_cep?.message ?? '8 dígitos numéricos, sem traço.'}
                {...registerEdit('endereco_cep')}
                sx={{ minWidth: 160 }}
              />
            </Stack>

            {updateClientMutation.isError ? (
              <Alert severity="error">
                {extractApiErrorMessage(
                  updateClientMutation.error,
                  errorMessages.clientUpdate,
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
              ? `Tem certeza de que deseja desativar o cliente ${selectedClient?.nome_fantasia}? Todos os usuários vinculados perderão o acesso.`
              : `Tem certeza de que deseja reativar o cliente ${selectedClient?.nome_fantasia}?`}
          </Typography>
          {toggleStatusMutation.isError ? (
            <Alert severity="error">
              {extractApiErrorMessage(
                toggleStatusMutation.error,
                errorMessages.clientUpdate,
              )}
            </Alert>
          ) : null}
        </Stack>
      </ConfirmationDialog>
    </>
  );
}
