import DeleteOutlineOutlinedIcon from '@mui/icons-material/DeleteOutlineOutlined';
import { Alert, Button, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

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
import { associationsApi } from '../../shared/services/api/associationsApi';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import { clientsApi } from '../../shared/services/api/clientsApi';
import { servicesApi } from '../../shared/services/api/servicesApi';
import { formatNumber, shortenUuid } from '../../shared/utils/format';
import { hasClientePerfil } from '../../shared/utils/permissions';

function formatAssociationOrigin(value: string) {
  return value
    .toLowerCase()
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export function AssociationsPage() {
  const { user, selectedClientId, setSelectedClientId } = useAuth();
  const { showMessage } = useFeedback();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedAssociationId, setSelectedAssociationId] = useState('');
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);

  const clientsQuery = useQuery({
    queryKey: ['clients', 'association-filter'],
    queryFn: () => clientsApi.list({ page: 1, page_size: 100 }),
    enabled: Boolean(user?.is_admin),
  });

  const associationsQuery = useQuery({
    queryKey: ['associations', selectedClientId, page, pageSize],
    queryFn: () =>
      associationsApi.list({
        cliente_id: selectedClientId,
        page,
        page_size: pageSize,
      }),
    enabled: Boolean(selectedClientId),
  });

  const associationRows = associationsQuery.data?.items ?? [];
  const selectedAssociation =
    associationRows.find((item) => item.id === selectedAssociationId) ??
    associationRows[0] ??
    null;

  const selectedServiceQuery = useQuery({
    queryKey: ['association-service', selectedAssociation?.servico_tcpo_id],
    queryFn: () => servicesApi.getById(selectedAssociation!.servico_tcpo_id),
    enabled: Boolean(selectedAssociation?.servico_tcpo_id),
  });

  const canDeleteSelected = Boolean(
    selectedAssociation &&
      (user?.is_admin ||
        hasClientePerfil(user, selectedAssociation.cliente_id, ['APROVADOR', 'ADMIN'])),
  );

  const deleteAssociationMutation = useMutation({
    mutationFn: () => associationsApi.remove(selectedAssociation!.id),
    onSuccess: () => {
      showMessage(successMessages.associationDeleted);
      setConfirmDeleteOpen(false);
      setSelectedAssociationId('');
      void queryClient.invalidateQueries({ queryKey: ['associations', selectedClientId] });
    },
  });

  if (!selectedClientId) {
    return (
      <>
        <PageHeader
          title="Associações Inteligentes"
          description="Gerencie os vínculos entre termos de busca e serviços do catálogo. As associações são aprendidas a cada busca realizada."
        />

        <Paper sx={{ p: 3, mb: 2, border: '1px solid', borderColor: 'divider' }}>
          {user?.is_admin ? (
            <TextField
              select
              fullWidth
              label="Cliente"
              value={selectedClientId}
              onChange={(event) => {
                setSelectedClientId(event.target.value);
                setPage(1);
              }}
              helperText="Selecione um cliente para consultar as associações registradas."
            >
              {clientsQuery.data?.items.map((client) => (
                <MenuItem key={client.id} value={client.id}>
                  {client.nome_fantasia} ({shortenUuid(client.id)})
                </MenuItem>
              )) ?? []}
            </TextField>
          ) : null}
        </Paper>

        <EmptyState
          title="Selecione um cliente antes de listar associações"
          description="Defina o cliente no topo ou no filtro desta tela para carregar a governança do ambiente correspondente."
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Associações Inteligentes"
        description="Revise vínculos aprendidos pelo sistema, acompanhe a frequência de uso e remova associações quando necessário."
      />

      <Stack direction={{ xs: 'column', xl: 'row' }} spacing={2}>
        <Paper sx={{ flex: 1.2, p: 3, border: '1px solid', borderColor: 'divider' }}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 2 }}>
            {user?.is_admin ? (
              <TextField
                select
                label="Cliente"
                value={selectedClientId}
                onChange={(event) => {
                  setSelectedClientId(event.target.value);
                  setPage(1);
                }}
                sx={{ minWidth: 320 }}
              >
                {clientsQuery.data?.items.map((client) => (
                  <MenuItem key={client.id} value={client.id}>
                    {client.nome_fantasia} ({shortenUuid(client.id)})
                  </MenuItem>
                )) ?? []}
              </TextField>
            ) : (
              <Alert severity="info" variant="outlined">
                Contexto do cliente carregado pela sessão autenticada.
              </Alert>
            )}
          </Stack>

          {associationsQuery.isError ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              {extractApiErrorMessage(associationsQuery.error, errorMessages.loadData)}
            </Alert>
          ) : null}

          <DataTable
            columns={[
              {
                key: 'texto',
                header: 'Termo',
                render: (row) => row.texto_busca_normalizado,
              },
              {
                key: 'servico',
                header: 'Serviço associado',
                render: (row) => shortenUuid(row.servico_tcpo_id),
              },
              {
                key: 'origem',
                header: 'Origem',
                render: (row) => formatAssociationOrigin(row.origem_associacao),
              },
              {
                key: 'frequencia',
                header: 'Frequência',
                align: 'right',
                render: (row) => row.frequencia_uso,
              },
              {
                key: 'status',
                header: 'Status',
                render: (row) => <StatusBadge value={row.status_validacao} />,
              },
              {
                key: 'score',
                header: 'Score',
                align: 'right',
                render: (row) =>
                  row.confiabilidade_score == null ? '-' : formatNumber(row.confiabilidade_score),
              },
            ]}
            rows={associationsQuery.data?.items ?? []}
            rowKey={(row) => row.id}
            loading={associationsQuery.isLoading}
            page={page}
            pageSize={pageSize}
            total={associationsQuery.data?.total ?? 0}
            emptyTitle="Nenhuma associação cadastrada"
            emptyDescription="As associações são criadas ao vincular termos a serviços durante a busca."
            onPageChange={setPage}
            onPageSizeChange={(value) => {
              setPageSize(value);
              setPage(1);
            }}
            onRowClick={(row) => setSelectedAssociationId(row.id)}
          />
        </Paper>

        <Paper sx={{ flex: 0.8, p: 3, border: '1px solid', borderColor: 'divider' }}>
          <Typography variant="h6" sx={{ mb: 1.5 }}>
            Detalhes da associação
          </Typography>

          {selectedAssociation ? (
            <Stack spacing={1.5}>
              <Typography variant="subtitle1">{selectedAssociation.texto_busca_normalizado}</Typography>
              <Typography variant="body2" color="text.secondary">
                Cliente: {shortenUuid(selectedAssociation.cliente_id)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Serviço vinculado: {shortenUuid(selectedAssociation.servico_tcpo_id)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Origem: {formatAssociationOrigin(selectedAssociation.origem_associacao)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Frequência de uso: {selectedAssociation.frequencia_uso}
              </Typography>
              <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                <StatusBadge value={selectedAssociation.status_validacao} />
              </Stack>

              {selectedServiceQuery.isError ? (
                <Alert severity="warning" variant="outlined">
                  {extractApiErrorMessage(selectedServiceQuery.error, errorMessages.loadData)}
                </Alert>
              ) : selectedServiceQuery.data ? (
                <Paper variant="outlined" sx={{ p: 1.5 }}>
                  <Typography variant="subtitle2">Serviço relacionado</Typography>
                  <Typography variant="body2">{selectedServiceQuery.data.descricao}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Código: {selectedServiceQuery.data.codigo_origem}
                  </Typography>
                </Paper>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Carregando dados do serviço relacionado...
                </Typography>
              )}

              {canDeleteSelected ? (
                <Button
                  variant="contained"
                  color="error"
                  startIcon={<DeleteOutlineOutlinedIcon />}
                  onClick={() => setConfirmDeleteOpen(true)}
                >
                  Excluir associação
                </Button>
              ) : (
                <Alert severity="info" variant="outlined">
                  A exclusão exige perfil Aprovador ou Administrador no cliente da associação.
                </Alert>
              )}
            </Stack>
          ) : (
            <EmptyState
              title="Nenhuma associação selecionada"
              description="Selecione uma linha da tabela para revisar o termo associado, o serviço vinculado e a governança de exclusão."
            />
          )}
        </Paper>
      </Stack>

      <ConfirmationDialog
        open={confirmDeleteOpen}
        title="Excluir associação"
        confirmLabel="Excluir"
        confirmColor="error"
        isLoading={deleteAssociationMutation.isPending}
        onCancel={() => setConfirmDeleteOpen(false)}
        onConfirm={() => deleteAssociationMutation.mutate()}
      >
        <Stack spacing={1}>
          <Typography variant="body2">Termo: {selectedAssociation?.texto_busca_normalizado}</Typography>
          <Typography variant="body2">
            Serviço: {selectedAssociation ? shortenUuid(selectedAssociation.servico_tcpo_id) : '-'}
          </Typography>
          {deleteAssociationMutation.isError ? (
            <Alert severity="error">
              {extractApiErrorMessage(deleteAssociationMutation.error, errorMessages.associationDelete)}
            </Alert>
          ) : null}
        </Stack>
      </ConfirmationDialog>
    </>
  );
}
