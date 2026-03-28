import {
  Alert,
  Button,
  CircularProgress,
  Paper,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from '@mui/material';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { useState } from 'react';
import { z } from 'zod';

import { useAuth } from '../auth/AuthProvider';
import { ConfirmationDialog } from '../../shared/components/ConfirmationDialog';
import { DataTable } from '../../shared/components/DataTable';
import { EmptyState } from '../../shared/components/EmptyState';
import {
  errorMessages,
  successMessages,
} from '../../shared/components/FeedbackMessages';
import { PageHeader } from '../../shared/components/PageHeader';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { homologationApi } from '../../shared/services/api/homologationApi';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import type { ItemPendenteResponse } from '../../shared/types/contracts/homologacao';
import { formatCurrency, formatDateTime } from '../../shared/utils/format';
import { hasClienteAccess, hasClientePerfil } from '../../shared/utils/permissions';

const createOwnItemSchema = z.object({
  codigo_origem: z.string().min(1, 'Informe o código do serviço.'),
  descricao: z.string().min(3, 'Informe a descrição do serviço.'),
  unidade_medida: z.string().min(1, 'Informe a unidade.'),
  custo_unitario: z.coerce.number().positive('Use um valor maior que zero.'),
  categoria_id: z.string().optional(),
});

type CreateOwnItemFormInput = z.input<typeof createOwnItemSchema>;
type CreateOwnItemFormOutput = z.output<typeof createOwnItemSchema>;
type PendingAction = { mode: 'approve' | 'reject'; item: ItemPendenteResponse } | null;

export function HomologationPage() {
  const { user, selectedClientId } = useAuth();
  const { showMessage } = useFeedback();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [pendingAction, setPendingAction] = useState<PendingAction>(null);
  const [motivoReprovacao, setMotivoReprovacao] = useState('');

  const canCreateOwnItem = hasClienteAccess(user, selectedClientId);
  const canHomologate = hasClientePerfil(user, selectedClientId, ['APROVADOR', 'ADMIN']);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<CreateOwnItemFormInput, undefined, CreateOwnItemFormOutput>({
    resolver: zodResolver(createOwnItemSchema),
    defaultValues: {
      codigo_origem: '',
      descricao: '',
      unidade_medida: '',
      custo_unitario: 0,
      categoria_id: '',
    },
  });

  const pendentesQuery = useQuery({
    queryKey: ['homologation', selectedClientId, page, pageSize],
    queryFn: () => homologationApi.listPendentes(selectedClientId, page, pageSize),
    enabled: Boolean(selectedClientId && canHomologate),
  });

  const createOwnItemMutation = useMutation({
    mutationFn: (values: CreateOwnItemFormOutput) =>
      homologationApi.criarItemProprio({
        cliente_id: selectedClientId,
        codigo_origem: values.codigo_origem,
        descricao: values.descricao,
        unidade_medida: values.unidade_medida,
        custo_unitario: values.custo_unitario,
        categoria_id: values.categoria_id ? Number(values.categoria_id) : null,
      }),
    onSuccess: () => {
      showMessage(successMessages.ownServiceCreated);
      reset();
      void queryClient.invalidateQueries({ queryKey: ['homologation'] });
    },
  });

  const approveMutation = useMutation({
    mutationFn: () =>
      homologationApi.aprovar({
        servico_id: pendingAction!.item.id,
        cliente_id: selectedClientId,
        aprovado: pendingAction?.mode === 'approve',
        motivo_reprovacao:
          pendingAction?.mode === 'reject' ? motivoReprovacao || undefined : undefined,
      }),
    onSuccess: (data) => {
      showMessage(data.mensagem);
      setPendingAction(null);
      setMotivoReprovacao('');
      void queryClient.invalidateQueries({ queryKey: ['homologation'] });
    },
  });

  if (!selectedClientId) {
    return (
      <>
        <PageHeader
          title="Homologação"
          description="Analise itens próprios pendentes e cadastre novos serviços para o cliente atual."
        />
        <EmptyState
          title="Defina o cliente antes de continuar"
          description="Selecione o cliente no topo para cadastrar serviços próprios e revisar pendências de homologação."
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Homologação"
        description="Cadastre itens próprios, aprove ou rejeite pendências e acompanhe o fluxo de validação do catálogo."
      />

      <Paper sx={{ mb: 2, border: '1px solid', borderColor: 'divider' }}>
        <Tabs value={tab} onChange={(_, value) => setTab(value)}>
          <Tab label="Pendentes" />
          <Tab label="Novo item próprio" />
        </Tabs>
      </Paper>

      {tab === 0 ? (
        canHomologate ? (
          <Paper sx={{ p: 3, border: '1px solid', borderColor: 'divider' }}>
            {pendentesQuery.isError ? (
              <Alert severity="error" sx={{ mb: 2 }}>
                {extractApiErrorMessage(pendentesQuery.error, errorMessages.loadData)}
              </Alert>
            ) : null}

            <DataTable
              columns={[
                { key: 'codigo', header: 'Código', render: (row) => row.codigo_origem },
                { key: 'descricao', header: 'Descrição', render: (row) => row.descricao },
                {
                  key: 'status',
                  header: 'Status',
                  render: (row) => <StatusBadge value={row.status_homologacao} />,
                },
                {
                  key: 'origem',
                  header: 'Origem',
                  render: (row) => row.origem,
                },
                {
                  key: 'custo',
                  header: 'Custo',
                  align: 'right',
                  render: (row) => formatCurrency(row.custo_unitario),
                },
                {
                  key: 'data',
                  header: 'Criado em',
                  render: (row) => formatDateTime(row.created_at),
                },
                {
                  key: 'acoes',
                  header: 'Ações',
                  render: (row) => (
                    <Stack direction="row" spacing={1}>
                      <Button
                        size="small"
                        variant="contained"
                        onClick={() => setPendingAction({ mode: 'approve', item: row })}
                      >
                        Aprovar
                      </Button>
                      <Button
                        size="small"
                        color="error"
                        variant="outlined"
                        onClick={() => setPendingAction({ mode: 'reject', item: row })}
                      >
                        Rejeitar
                      </Button>
                    </Stack>
                  ),
                },
              ]}
              rows={pendentesQuery.data?.items ?? []}
              rowKey={(row) => row.id}
              loading={pendentesQuery.isLoading}
              page={page}
              pageSize={pageSize}
              total={pendentesQuery.data?.total ?? 0}
              emptyTitle="Nenhum serviço pendente"
              emptyDescription="Não há serviços aguardando homologação no momento."
              onPageChange={setPage}
              onPageSizeChange={(value) => {
                setPageSize(value);
                setPage(1);
              }}
            />
          </Paper>
        ) : (
          <EmptyState
            title="Perfil insuficiente para homologação"
            description="A listagem de pendentes está disponível apenas para aprovadores e administradores do cliente atual."
          />
        )
      ) : canCreateOwnItem ? (
        <Paper sx={{ p: 3, border: '1px solid', borderColor: 'divider' }}>
          <Stack
            component="form"
            spacing={2}
            onSubmit={handleSubmit((values) => createOwnItemMutation.mutate(values))}
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
            <Typography variant="body2" color="text.secondary">
              Este serviço será criado como PROPRIA e ficará pendente até a análise de homologação.
            </Typography>
            <Button type="submit" variant="contained" disabled={createOwnItemMutation.isPending}>
              {createOwnItemMutation.isPending ? (
                <CircularProgress size={20} color="inherit" />
              ) : (
                'Salvar'
              )}
            </Button>
            {createOwnItemMutation.isError ? (
              <Alert severity="error">
                {extractApiErrorMessage(createOwnItemMutation.error, errorMessages.serviceSave)}
              </Alert>
            ) : null}
          </Stack>
        </Paper>
      ) : (
        <EmptyState
          title="Sem acesso ao cliente atual"
          description="Você precisa de vínculo com o cliente selecionado para cadastrar itens próprios."
        />
      )}

      <ConfirmationDialog
        open={Boolean(pendingAction)}
        title={pendingAction?.mode === 'approve' ? 'Aprovar serviço' : 'Rejeitar serviço'}
        confirmLabel={pendingAction?.mode === 'approve' ? 'Aprovar' : 'Rejeitar'}
        confirmColor={pendingAction?.mode === 'approve' ? 'primary' : 'error'}
        isLoading={approveMutation.isPending}
        onCancel={() => {
          setPendingAction(null);
          setMotivoReprovacao('');
        }}
        onConfirm={() => approveMutation.mutate()}
      >
        <Stack spacing={2}>
          <Typography variant="body2">Serviço: {pendingAction?.item.descricao}</Typography>
          {pendingAction?.mode === 'reject' ? (
            <TextField
              label="Motivo da rejeição"
              multiline
              minRows={3}
              value={motivoReprovacao}
              onChange={(event) => setMotivoReprovacao(event.target.value)}
            />
          ) : null}
          {approveMutation.isError ? (
            <Alert severity="error">
              {extractApiErrorMessage(approveMutation.error, errorMessages.loadData)}
            </Alert>
          ) : null}
        </Stack>
      </ConfirmationDialog>
    </>
  );
}
