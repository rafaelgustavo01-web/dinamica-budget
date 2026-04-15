import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import ToggleOffOutlinedIcon from '@mui/icons-material/ToggleOffOutlined';
import ToggleOnOutlinedIcon from '@mui/icons-material/ToggleOnOutlined';
import {
  Alert,
  Button,
  Checkbox,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
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
import { PageHeader } from '../../shared/components/PageHeader';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import { clientsApi } from '../../shared/services/api/clientsApi';
import { userApi } from '../../shared/services/api/userApi';
import type { PerfilUsuario, UsuarioCreate } from '../../shared/types/contracts/auth';
import type { ClienteResponse } from '../../shared/types/contracts/clientes';
import type { UsuarioPatchRequest } from '../../shared/types/contracts/usuarios';
import { getPerfilLabel, shortenUuid } from '../../shared/utils/format';

const PROFILE_OPTIONS = ['USUARIO', 'APROVADOR', 'ADMIN'] as const;
type ManagedPerfil = (typeof PROFILE_OPTIONS)[number];
type StatusFilter = 'all' | 'active' | 'inactive';

const createUserSchema = z.object({
  nome: z.string().min(3, 'Informe o nome completo.'),
  email: z.email('Informe um email valido.'),
  password: z.string().min(8, 'Use ao menos 8 caracteres.'),
  is_admin: z.boolean(),
});

const editUserSchema = z.object({
  nome: z.string().min(1, 'Informe o nome do usuario.'),
  email: z.email('Informe um email valido.'),
  is_admin: z.boolean(),
});

type CreateUserFormValues = z.infer<typeof createUserSchema>;
type EditUserFormValues = z.infer<typeof editUserSchema>;

function getUserStatusLabel(isActive: boolean) {
  return isActive ? 'Ativo' : 'Inativo';
}

function findClientName(clientId: string, clients: ClienteResponse[]) {
  return clients.find((item) => item.id === clientId)?.nome_fantasia ?? shortenUuid(clientId);
}

export function UsersPage() {
  const { showMessage } = useFeedback();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [confirmStatusOpen, setConfirmStatusOpen] = useState(false);
  const [perfilClientId, setPerfilClientId] = useState('');
  const [selectedPerfis, setSelectedPerfis] = useState<ManagedPerfil[]>([]);
  const [hasPerfisDraft, setHasPerfisDraft] = useState(false);

  const {
    register: registerCreate,
    handleSubmit: handleCreateSubmit,
    formState: { errors: createErrors },
    reset: resetCreateForm,
  } = useForm<CreateUserFormValues>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      nome: '',
      email: '',
      password: '',
      is_admin: false,
    },
  });

  const {
    register: registerEdit,
    handleSubmit: handleEditSubmit,
    formState: { errors: editErrors },
    reset: resetEditForm,
  } = useForm<EditUserFormValues>({
    resolver: zodResolver(editUserSchema),
    defaultValues: {
      nome: '',
      email: '',
      is_admin: false,
    },
  });

  const usersQuery = useQuery({
    queryKey: ['users', statusFilter, page, pageSize],
    queryFn: () =>
      userApi.list({
        page,
        page_size: pageSize,
        is_active:
          statusFilter === 'all' ? undefined : statusFilter === 'active',
      }),
  });
  const userRows = usersQuery.data?.items ?? [];
  const selectedUser =
    userRows.find((item) => item.id === selectedUserId) ?? userRows[0] ?? null;

  const clientsQuery = useQuery({
    queryKey: ['clients', 'user-rbac'],
    queryFn: () => clientsApi.list({ page: 1, page_size: 100 }),
  });

  const perfisQuery = useQuery({
    queryKey: ['users', 'perfis', selectedUser?.id],
    queryFn: () => userApi.getPerfis(selectedUser!.id),
    enabled: Boolean(selectedUser?.id),
  });
  const knownClients = clientsQuery.data?.items ?? [];
  const knownClientIds = knownClients.map((item) => item.id);
  const boundClientIds = Array.from(
    new Set((perfisQuery.data?.perfis ?? []).map((item) => item.cliente_id)),
  );
  const effectivePerfilClientId =
    perfilClientId && (knownClientIds.includes(perfilClientId) || boundClientIds.includes(perfilClientId))
      ? perfilClientId
      : boundClientIds[0] ?? knownClientIds[0] ?? '';
  const currentPerfisForClient = (perfisQuery.data?.perfis ?? [])
    .filter((item) => item.cliente_id === effectivePerfilClientId)
    .map((item) => item.perfil)
    .filter((perfil): perfil is ManagedPerfil =>
      PROFILE_OPTIONS.includes(perfil as ManagedPerfil),
    );
  const activePerfis = hasPerfisDraft ? selectedPerfis : currentPerfisForClient;

  const createUserMutation = useMutation({
    mutationFn: (values: UsuarioCreate) => userApi.create(values),
    onSuccess: () => {
      showMessage(successMessages.userCreated);
      setCreateDialogOpen(false);
      resetCreateForm();
      void queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  const updateUserMutation = useMutation({
    mutationFn: (payload: UsuarioPatchRequest) => userApi.update(selectedUser!.id, payload),
    onSuccess: (data) => {
      showMessage(successMessages.userUpdated);
      setSelectedUserId(data.id);
      setEditDialogOpen(false);
      void queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  const toggleStatusMutation = useMutation({
    mutationFn: () =>
      userApi.update(selectedUser!.id, {
        is_active: !selectedUser!.is_active,
      }),
    onSuccess: (data) => {
      showMessage(data.is_active ? successMessages.userActivated : successMessages.userDeactivated);
      setSelectedUserId(data.id);
      setConfirmStatusOpen(false);
      void queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  const setPerfisMutation = useMutation({
    mutationFn: (perfis: ManagedPerfil[]) =>
      userApi.setPerfis(selectedUser!.id, {
        cliente_id: effectivePerfilClientId,
        perfis,
      }),
    onSuccess: () => {
      showMessage(successMessages.userPerfisUpdated);
      setSelectedPerfis([]);
      setHasPerfisDraft(false);
      void queryClient.invalidateQueries({ queryKey: ['users', 'perfis', selectedUser?.id] });
    },
  });

  const groupedPerfis = Array.from(
    (perfisQuery.data?.perfis ?? []).reduce((map, item) => {
      const current = map.get(item.cliente_id) ?? [];
      current.push(item.perfil);
      map.set(item.cliente_id, current);
      return map;
    }, new Map<string, PerfilUsuario[]>()),
  );

  return (
    <>
      <PageHeader
        title="Usuários"
        description="Gerencie os usuários do sistema e seus perfis de acesso. Cada usuário é vinculado a um cliente e possui um nível de permissão."
        actions={
          <Button
            variant="contained"
            startIcon={<AddOutlinedIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Novo usuário
          </Button>
        }
      />

      <Stack direction={{ xs: 'column', xl: 'row' }} spacing={2}>
        <Paper sx={{ flex: 1.15, p: 3 }}>
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

          {usersQuery.isError ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              {extractApiErrorMessage(usersQuery.error, 'Falha ao carregar os usuarios.')}
            </Alert>
          ) : null}

          <DataTable
            columns={[
              {
                key: 'nome',
                header: 'Nome',
                render: (row) => row.nome,
              },
              {
                key: 'email',
                header: 'Email',
                render: (row) => row.email,
              },
              {
                key: 'status',
                header: 'Status',
                render: (row) => getUserStatusLabel(row.is_active),
              },
              {
                key: 'admin',
                header: 'Admin',
                render: (row) => (row.is_admin ? 'Sim' : 'Nao'),
              },
            ]}
            rows={usersQuery.data?.items ?? []}
            rowKey={(row) => row.id}
            loading={usersQuery.isLoading}
            page={page}
            pageSize={pageSize}
            total={usersQuery.data?.total ?? 0}
            emptyTitle="Nenhum usuário cadastrado"
            emptyDescription="Cadastre usuários e defina perfis de acesso para começar a usar o sistema."
            onPageChange={setPage}
            onPageSizeChange={(value) => {
              setPageSize(value);
              setPage(1);
            }}
            onRowClick={(row) => {
              setSelectedUserId(row.id);
              setPerfilClientId('');
              setSelectedPerfis([]);
              setHasPerfisDraft(false);
            }}
          />
        </Paper>

        <Paper sx={{ flex: 0.85, p: 3 }}>
          <Typography variant="h6" sx={{ mb: 1.5 }}>
            Gestão administrativa
          </Typography>

          {selectedUser ? (
            <Stack spacing={2}>
              <Stack spacing={0.5}>
                <Typography variant="subtitle1">{selectedUser.nome}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Email: {selectedUser.email}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Status: {getUserStatusLabel(selectedUser.is_active)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Admin global: {selectedUser.is_admin ? 'Sim' : 'Nao'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  ID: {shortenUuid(selectedUser.id)}
                </Typography>
                {selectedUser.external_id_ad ? (
                  <Typography variant="body2" color="text.secondary">
                    AD externo: {selectedUser.external_id_ad}
                  </Typography>
                ) : null}
              </Stack>

              <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
                <Button
                  variant="outlined"
                  startIcon={<EditOutlinedIcon />}
                  onClick={() => {
                    resetEditForm({
                      nome: selectedUser.nome,
                      email: selectedUser.email,
                      is_admin: selectedUser.is_admin,
                    });
                    setEditDialogOpen(true);
                  }}
                >
                  Editar dados
                </Button>
                <Button
                  variant="outlined"
                  color={selectedUser.is_active ? 'warning' : 'success'}
                  startIcon={
                    selectedUser.is_active ? <ToggleOffOutlinedIcon /> : <ToggleOnOutlinedIcon />
                  }
                  onClick={() => setConfirmStatusOpen(true)}
                >
                  {selectedUser.is_active ? 'Inativar' : 'Reativar'}
                </Button>
              </Stack>

              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1.5 }}>
                  Perfis por cliente
                </Typography>

                {perfisQuery.isError ? (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    {extractApiErrorMessage(
                      perfisQuery.error,
                      'Falha ao carregar os perfis por cliente.',
                    )}
                  </Alert>
                ) : null}

                {perfisQuery.isLoading ? (
                  <Typography variant="body2" color="text.secondary">
                    Carregando perfis por cliente...
                  </Typography>
                ) : groupedPerfis.length ? (
                  <Stack spacing={1.5}>
                    {groupedPerfis.map(([clientId, perfis]) => (
                      <Paper key={clientId} variant="outlined" sx={{ p: 1.5 }}>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          {findClientName(clientId, knownClients)}
                        </Typography>
                        <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                          {perfis.map((perfil) => (
                            <Chip key={`${clientId}-${perfil}`} size="small" label={getPerfilLabel(perfil)} />
                          ))}
                        </Stack>
                      </Paper>
                    ))}
                  </Stack>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    Este usuario ainda nao possui vinculos de RBAC por cliente.
                  </Typography>
                )}
              </Paper>

              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1.5 }}>
                  Atualizar perfis em um cliente
                </Typography>

                <Stack spacing={1.5}>
                  <TextField
                    select
                    label="Cliente"
                    value={effectivePerfilClientId}
                    onChange={(event) => {
                      setPerfilClientId(event.target.value);
                      setSelectedPerfis([]);
                      setHasPerfisDraft(false);
                    }}
                    disabled={!knownClients.length && !groupedPerfis.length}
                  >
                    {knownClients.map((client) => (
                      <MenuItem key={client.id} value={client.id}>
                        {client.nome_fantasia} ({shortenUuid(client.id)})
                      </MenuItem>
                    ))}
                    {groupedPerfis
                      .filter(([clientId]) => !knownClients.some((client) => client.id === clientId))
                      .map(([clientId]) => (
                        <MenuItem key={clientId} value={clientId}>
                          {shortenUuid(clientId)}
                        </MenuItem>
                      ))}
                  </TextField>

                  <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                    {PROFILE_OPTIONS.map((perfil) => (
                      <FormControlLabel
                        key={perfil}
                        control={
                          <Checkbox
                            checked={activePerfis.includes(perfil)}
                            onChange={(event) => {
                              const nextPerfis = event.target.checked
                                ? Array.from(new Set([...activePerfis, perfil]))
                                : activePerfis.filter((item) => item !== perfil);

                              setHasPerfisDraft(true);
                              setSelectedPerfis(nextPerfis);
                            }}
                          />
                        }
                        label={getPerfilLabel(perfil)}
                      />
                    ))}
                  </Stack>

                  {!effectivePerfilClientId ? (
                    <Alert severity="info" variant="outlined">
                      Selecione um cliente para substituir os perfis do usuario naquela conta.
                    </Alert>
                  ) : null}

                  <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
                    <Button
                      variant="contained"
                      disabled={!effectivePerfilClientId || setPerfisMutation.isPending}
                      onClick={() => setPerfisMutation.mutate(activePerfis)}
                    >
                      Salvar perfis
                    </Button>
                    <Button
                      variant="outlined"
                      color="warning"
                      disabled={!effectivePerfilClientId || setPerfisMutation.isPending}
                      onClick={() => setPerfisMutation.mutate([])}
                    >
                      Revogar acessos do cliente
                    </Button>
                  </Stack>

                  {setPerfisMutation.isError ? (
                    <Alert severity="error">
                      {extractApiErrorMessage(
                        setPerfisMutation.error,
                        'Falha ao atualizar os perfis do usuario.',
                      )}
                    </Alert>
                  ) : null}
                </Stack>
              </Paper>
            </Stack>
          ) : (
            <EmptyState
              title="Nenhum usuario selecionado"
              description="Selecione um usuário na tabela para editar dados básicos, alterar status e administrar perfis por cliente."
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
        <DialogTitle>Novo usuário</DialogTitle>
        <DialogContent dividers>
          <Stack
            component="form"
            spacing={2}
            sx={{ mt: 0.5 }}
            onSubmit={handleCreateSubmit((values) => createUserMutation.mutate(values))}
          >
            <TextField
              label="Nome"
              error={Boolean(createErrors.nome)}
              helperText={createErrors.nome?.message}
              {...registerCreate('nome')}
            />
            <TextField
              label="Email"
              type="email"
              error={Boolean(createErrors.email)}
              helperText={createErrors.email?.message}
              {...registerCreate('email')}
            />
            <TextField
              label="Senha"
              type="password"
              error={Boolean(createErrors.password)}
              helperText={createErrors.password?.message ?? 'Use ao menos 8 caracteres.'}
              {...registerCreate('password')}
            />
            <FormControlLabel
              control={<Checkbox {...registerCreate('is_admin')} />}
              label="Usuário administrativo"
            />
            {createUserMutation.isError ? (
              <Alert severity="error">
                {extractApiErrorMessage(
                  createUserMutation.error,
                  errorMessages.userCreate,
                )}
              </Alert>
            ) : null}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={handleCreateSubmit((values) => createUserMutation.mutate(values))}
            disabled={createUserMutation.isPending}
          >
            {createUserMutation.isPending ? (
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
        <DialogTitle>Editar usuário</DialogTitle>
        <DialogContent dividers>
          <Stack
            component="form"
            spacing={2}
            sx={{ mt: 0.5 }}
            onSubmit={handleEditSubmit((values) => updateUserMutation.mutate(values))}
          >
            <TextField
              label="Nome"
              error={Boolean(editErrors.nome)}
              helperText={editErrors.nome?.message}
              {...registerEdit('nome')}
            />
            <TextField
              label="Email"
              type="email"
              error={Boolean(editErrors.email)}
              helperText={editErrors.email?.message}
              {...registerEdit('email')}
            />
            <FormControlLabel
              control={<Checkbox {...registerEdit('is_admin')} />}
              label="Usuário administrativo"
            />
            {updateUserMutation.isError ? (
              <Alert severity="error">
                {extractApiErrorMessage(
                  updateUserMutation.error,
                  errorMessages.userUpdate,
                )}
              </Alert>
            ) : null}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={handleEditSubmit((values) => updateUserMutation.mutate(values))}
            disabled={updateUserMutation.isPending}
          >
            {updateUserMutation.isPending ? (
              <CircularProgress size={20} color="inherit" />
            ) : (
              'Salvar'
            )}
          </Button>
        </DialogActions>
      </Dialog>

      <ConfirmationDialog
        open={confirmStatusOpen}
        title={selectedUser?.is_active ? 'Desativar usuário' : 'Reativar usuário'}
        confirmLabel={selectedUser?.is_active ? 'Inativar' : 'Reativar'}
        confirmColor={selectedUser?.is_active ? 'error' : 'primary'}
        isLoading={toggleStatusMutation.isPending}
        onCancel={() => setConfirmStatusOpen(false)}
        onConfirm={() => toggleStatusMutation.mutate()}
      >
        <Stack spacing={1}>
          <Typography variant="body2">
            Usuário: {selectedUser?.nome}
          </Typography>
          <Typography variant="body2">
            Email: {selectedUser?.email}
          </Typography>
          {toggleStatusMutation.isError ? (
            <Alert severity="error">
              {extractApiErrorMessage(
                toggleStatusMutation.error,
                errorMessages.userUpdate,
              )}
            </Alert>
          ) : null}
        </Stack>
      </ConfirmationDialog>
    </>
  );
}
