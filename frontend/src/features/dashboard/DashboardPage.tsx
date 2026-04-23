import { Alert, Box, Paper, Stack, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';

import { EmptyState } from '../../shared/components/EmptyState';
import { PageHeader } from '../../shared/components/PageHeader';
import { useAuth } from '../auth/AuthProvider';
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
    <Paper
      sx={{
        p: 3,
        border: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h3" sx={{ mt: 1.25, mb: 0.75 }}>
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
    Boolean(selectedClientId) && hasClientePerfil(user, selectedClientId, ['APROVADOR', 'ADMIN']);

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
          description="Acompanhe indicadores operacionais, pendências e o contexto atual da sua sessão."
        />
        <EmptyState
          title="Selecione um cliente para começar"
          description="Defina o cliente no topo para carregar métricas, pendências de homologação e o catálogo disponível para a operação."
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Visão resumida do ambiente autenticado, com indicadores úteis para o trabalho diário."
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
          helper="Total de serviços disponíveis no recorte atual."
        />
        <MetricCard
          label="Pendências de homologação"
          value={String(homologationQuery.data?.total ?? 0)}
          helper={
            canSeeHomologation
              ? 'Itens aguardando análise do aprovador.'
              : 'Disponível para aprovadores e administradores.'
          }
        />
        <MetricCard
          label="Clientes vinculados"
          value={String(user?.perfis.filter((perfil) => perfil.cliente_id !== '*').length ?? 0)}
          helper="Perfis carregados a partir do contexto autenticado."
        />
        <MetricCard
          label="Perfil dominante"
          value={user?.is_admin ? 'Administrador' : getPerfilLabel(user?.perfis[0]?.perfil ?? 'USUARIO')}
          helper="Definido pelo backend de autenticação."
        />
      </Box>

      <Stack direction={{ xs: 'column', xl: 'row' }} spacing={2} sx={{ mt: 2 }}>
        <Paper sx={{ flex: 1, p: 3, border: '1px solid', borderColor: 'divider' }}>
          <Typography variant="h6" sx={{ mb: 1.5 }}>
            Contexto atual
          </Typography>
          <Stack spacing={1}>
            <Typography variant="body2" color="text.secondary">
              Usuário: {user?.nome} ({user?.email})
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Cliente ativo: {selectedClientId || 'Administrador sem escopo específico'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Módulos operacionais disponíveis: catálogo, busca inteligente, homologação,
              composições, associações e governança administrativa.
            </Typography>
          </Stack>
        </Paper>

        <Paper sx={{ flex: 1, p: 3, border: '1px solid', borderColor: 'divider' }}>
          <Typography variant="h6" sx={{ mb: 1.5 }}>
            Status da Plataforma
          </Typography>
          <Stack spacing={1}>
            <Typography variant="body2" color="text.secondary">
              Módulos de Usuários, Clientes, Relatórios e Perfil estão operacionais.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              A manutenção de permissões por cliente (RBAC) está centralizada na gestão de usuários.
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
