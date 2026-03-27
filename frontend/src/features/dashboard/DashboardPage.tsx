import {
  Alert,
  Box,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';

import { useAuth } from '../auth/AuthProvider';
import { EmptyState } from '../../shared/components/EmptyState';
import { PageHeader } from '../../shared/components/PageHeader';
import { homologationApi } from '../../shared/services/api/homologationApi';
import { servicesApi } from '../../shared/services/api/servicesApi';
import { getPerfilLabel } from '../../shared/utils/format';
import { hasClientePerfil } from '../../shared/utils/permissions';

function MetricCard({
  label,
  value,
  helper,
}: {
  label: string;
  value: string;
  helper: string;
}) {
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h3" sx={{ mt: 1.2, mb: 1 }}>
        {value}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        {helper}
      </Typography>
    </Paper>
  );
}

export function DashboardPage() {
  const { user, selectedClientId } = useAuth();
  const canSeeHomologation =
    Boolean(selectedClientId) &&
    hasClientePerfil(user, selectedClientId, ['APROVADOR', 'ADMIN']);

  const servicesQuery = useQuery({
    queryKey: ['dashboard', 'services', selectedClientId],
    queryFn: () =>
      servicesApi.list({
        page: 1,
        page_size: 10,
        cliente_id: selectedClientId || undefined,
      }),
    enabled: Boolean(user && (selectedClientId || user.is_admin)),
  });

  const homologationQuery = useQuery({
    queryKey: ['dashboard', 'homologation', selectedClientId],
    queryFn: () => homologationApi.listPendentes(selectedClientId, 1, 10),
    enabled: canSeeHomologation,
  });

  if (!selectedClientId && !user?.is_admin) {
    return (
      <>
        <PageHeader
          title="Dashboard"
          description="Resumo operacional do ambiente autenticado."
        />
        <EmptyState
          title="Selecione um cliente para começar"
          description="Esta visão operacional usa o cliente selecionado como contexto principal. Defina o escopo no topo antes de navegar pelos módulos."
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Visão resumida do ambiente autenticado, dos módulos disponíveis e do contexto operacional atual."
      />

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', xl: 'repeat(4, minmax(0, 1fr))' },
          gap: 2,
        }}
      >
        <MetricCard
          label="Catálogo visível"
          value={String(servicesQuery.data?.total ?? 0)}
          helper="Total retornado hoje pelo endpoint oficial de listagem."
        />
        <MetricCard
          label="Pendências de homologação"
          value={String(homologationQuery.data?.total ?? 0)}
          helper={
            canSeeHomologation
              ? 'Itens próprios aguardando decisão no cliente ativo.'
              : 'Visível apenas para aprovador ou administrador.'
          }
        />
        <MetricCard
          label="Clientes vinculados"
          value={String(user?.perfis.filter((perfil) => perfil.cliente_id !== '*').length ?? 0)}
          helper="Perfis carregados a partir de /auth/me."
        />
        <MetricCard
          label="Perfil dominante"
          value={user?.is_admin ? 'ADMIN' : getPerfilLabel(user?.perfis[0]?.perfil ?? '-')}
          helper="Determinado exclusivamente pelo backend."
        />
      </Box>

      <Stack direction={{ xs: 'column', xl: 'row' }} spacing={2} sx={{ mt: 2 }}>
        <Paper sx={{ flex: 1, p: 3 }}>
          <Typography variant="h6" sx={{ mb: 1.5 }}>
            Contexto atual
          </Typography>
          <Stack spacing={1}>
            <Typography variant="body2" color="text.secondary">
              Usuário: {user?.nome} ({user?.email})
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Cliente ativo: {selectedClientId || 'Admin sem escopo de cliente'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Módulos operacionais já integrados: autenticação, serviços, busca,
              associações, homologação, composições, usuários, clientes e administração.
            </Typography>
          </Stack>
        </Paper>

        <Paper sx={{ flex: 1, p: 3 }}>
          <Typography variant="h6" sx={{ mb: 1.5 }}>
            Gaps de contrato identificados
          </Typography>
          <Stack spacing={1}>
            <Typography variant="body2" color="text.secondary">
              Clientes já possuem listagem, cadastro, edição e status. Usuários já
              possuem criação, listagem, edição, status e perfis por cliente.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Ainda dependem de contratos adicionais: autoedição de perfil,
              relatórios dedicados e um módulo separado de permissões.
            </Typography>
          </Stack>
        </Paper>
      </Stack>

      {servicesQuery.isError ? (
        <Alert severity="warning" sx={{ mt: 2 }}>
          Não foi possível carregar o resumo do catálogo com o contexto atual.
        </Alert>
      ) : null}
    </>
  );
}
