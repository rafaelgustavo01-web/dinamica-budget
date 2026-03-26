import FileDownloadOutlinedIcon from '@mui/icons-material/FileDownloadOutlined';
import {
  Alert,
  Button,
  Paper,
  Stack,
  Tab,
  Tabs,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { useAuth } from '../auth/AuthProvider';
import { ContractNotice } from '../../shared/components/ContractNotice';
import { DataTable } from '../../shared/components/DataTable';
import { EmptyState } from '../../shared/components/EmptyState';
import { PageHeader } from '../../shared/components/PageHeader';
import { homologationApi } from '../../shared/services/api/homologationApi';
import { servicesApi } from '../../shared/services/api/servicesApi';
import { downloadCsv } from '../../shared/utils/csv';
import { formatCurrency, formatDateTime } from '../../shared/utils/format';
import { hasClientePerfil } from '../../shared/utils/permissions';

export function ReportsPage() {
  const { user, selectedClientId } = useAuth();
  const [tab, setTab] = useState(0);

  const servicesReportQuery = useQuery({
    queryKey: ['reports', 'services', selectedClientId],
    queryFn: () =>
      servicesApi.list({
        page: 1,
        page_size: 50,
        cliente_id: selectedClientId || undefined,
      }),
    enabled: Boolean(user && (selectedClientId || user.is_admin)),
  });

  const homologationReportQuery = useQuery({
    queryKey: ['reports', 'homologation', selectedClientId],
    queryFn: () => homologationApi.listPendentes(selectedClientId, 1, 50),
    enabled:
      Boolean(selectedClientId) &&
      hasClientePerfil(user, selectedClientId, ['APROVADOR', 'ADMIN']),
  });

  if (!selectedClientId && !user?.is_admin) {
    return (
      <>
        <PageHeader
          title="Relatórios"
          description="Visão tabular de consultas operacionais suportadas pelo backend atual."
        />
        <EmptyState
          title="Selecione um cliente para gerar relatórios operacionais"
          description="Os relatórios implementados hoje partem das listagens oficiais já publicadas pelo backend."
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Relatórios"
        description="Camada tabular prática para as consultas já disponíveis hoje, com exportação CSV do recorte carregado."
      />

      <Paper sx={{ mb: 2 }}>
        <Tabs value={tab} onChange={(_, value) => setTab(value)}>
          <Tab label="Serviços visíveis" />
          <Tab label="Pendências de homologação" />
        </Tabs>
      </Paper>

      {tab === 0 ? (
        <Stack spacing={2}>
          <Paper sx={{ p: 2 }}>
            <Stack direction="row" justifyContent="flex-end">
              <Button
                startIcon={<FileDownloadOutlinedIcon />}
                onClick={() =>
                  downloadCsv(
                    'relatorio-servicos.csv',
                    ['Código', 'Descrição', 'Unidade', 'Categoria', 'Custo'],
                    (servicesReportQuery.data?.items ?? []).map((item) => [
                      item.codigo_origem,
                      item.descricao,
                      item.unidade_medida,
                      item.categoria_id ?? '-',
                      String(item.custo_unitario),
                    ]),
                  )
                }
              >
                Exportar CSV
              </Button>
            </Stack>
          </Paper>

          {servicesReportQuery.isError ? (
            <Alert severity="error">Falha ao carregar o relatório de serviços.</Alert>
          ) : null}

          <DataTable
            columns={[
              { key: 'codigo', header: 'Código', render: (row) => row.codigo_origem },
              { key: 'descricao', header: 'Descrição', render: (row) => row.descricao },
              { key: 'unidade', header: 'Unidade', render: (row) => row.unidade_medida },
              { key: 'categoria', header: 'Categoria', render: (row) => row.categoria_id ?? '-' },
              {
                key: 'custo',
                header: 'Custo',
                align: 'right',
                render: (row) => formatCurrency(row.custo_unitario),
              },
            ]}
            rows={servicesReportQuery.data?.items ?? []}
            rowKey={(row) => row.id}
            loading={servicesReportQuery.isLoading}
            page={1}
            pageSize={Math.max(servicesReportQuery.data?.items.length ?? 1, 1)}
            total={servicesReportQuery.data?.items.length ?? 0}
            emptyTitle="Relatório sem itens"
            emptyDescription="Nenhum serviço visível foi retornado para o recorte atual."
          />
        </Stack>
      ) : (
        <Stack spacing={2}>
          <Paper sx={{ p: 2 }}>
            <Stack direction="row" justifyContent="flex-end">
              <Button
                startIcon={<FileDownloadOutlinedIcon />}
                onClick={() =>
                  downloadCsv(
                    'relatorio-homologacao.csv',
                    ['Código', 'Descrição', 'Origem', 'Status', 'Criado em'],
                    (homologationReportQuery.data?.items ?? []).map((item) => [
                      item.codigo_origem,
                      item.descricao,
                      item.origem,
                      item.status_homologacao,
                      formatDateTime(item.created_at),
                    ]),
                  )
                }
              >
                Exportar CSV
              </Button>
            </Stack>
          </Paper>

          <DataTable
            columns={[
              { key: 'codigo', header: 'Código', render: (row) => row.codigo_origem },
              { key: 'descricao', header: 'Descrição', render: (row) => row.descricao },
              { key: 'origem', header: 'Origem', render: (row) => row.origem },
              { key: 'status', header: 'Status', render: (row) => row.status_homologacao },
              {
                key: 'data',
                header: 'Criado em',
                render: (row) => formatDateTime(row.created_at),
              },
            ]}
            rows={homologationReportQuery.data?.items ?? []}
            rowKey={(row) => row.id}
            loading={homologationReportQuery.isLoading}
            page={1}
            pageSize={Math.max(homologationReportQuery.data?.items.length ?? 1, 1)}
            total={homologationReportQuery.data?.items.length ?? 0}
            emptyTitle="Sem pendências disponíveis"
            emptyDescription="Este relatório depende de perfil aprovador no cliente atual."
          />
        </Stack>
      )}

      <Stack spacing={2} sx={{ mt: 2 }}>
        <ContractNotice
          title="Cobertura de relatórios ainda parcial"
          description="Os relatórios operacionais implementados hoje reutilizam os endpoints já existentes de serviços e homologação. As demais tabelas aguardam APIs dedicadas ou listagens publicadas."
          missingContracts={[
            'GET /relatorios/usuarios',
            'GET /relatorios/clientes',
            'GET /relatorios/associacoes',
            'GET /relatorios/buscas',
            'GET /relatorios/composicoes',
          ]}
          availableNow={[
            'Listagem de catálogo via GET /servicos/',
            'Pendências via GET /homologacao/pendentes',
          ]}
        />
      </Stack>
    </>
  );
}
