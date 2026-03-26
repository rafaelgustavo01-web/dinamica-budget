import {
  Alert,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { useAuth } from '../auth/AuthProvider';
import { ContractNotice } from '../../shared/components/ContractNotice';
import { DataTable } from '../../shared/components/DataTable';
import { EmptyState } from '../../shared/components/EmptyState';
import { PageHeader } from '../../shared/components/PageHeader';
import { servicesApi } from '../../shared/services/api/servicesApi';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import type { ServicoTcpoResponse } from '../../shared/types/contracts/servicos';
import { formatCurrency } from '../../shared/utils/format';

export function CompositionsPage() {
  const { user, selectedClientId } = useAuth();
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedService, setSelectedService] = useState<ServicoTcpoResponse | null>(null);

  const servicesQuery = useQuery({
    queryKey: ['composition-page', selectedClientId, query, page, pageSize],
    queryFn: () =>
      servicesApi.list({
        page,
        page_size: pageSize,
        q: query || undefined,
        cliente_id: selectedClientId || undefined,
      }),
    enabled: Boolean(user && (selectedClientId || user.is_admin)),
  });

  const compositionQuery = useQuery({
    queryKey: ['composition-page', 'composition', selectedService?.id],
    queryFn: () => servicesApi.getComposicao(selectedService!.id),
    enabled: Boolean(selectedService?.id),
  });

  if (!selectedClientId && !user?.is_admin) {
    return (
      <>
        <PageHeader
          title="Composições"
          description="Visualização operacional da estrutura pai-filho de serviços."
        />
        <EmptyState
          title="Selecione um cliente para consultar o catálogo visível"
          description="O frontend mantém o recorte por cliente para evitar consumo fora do escopo do usuário."
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Composições"
        description="Visualização de composição existente com base nos endpoints publicados de catálogo e explosão."
      />

      <Stack direction={{ xs: 'column', xl: 'row' }} spacing={2}>
        <Paper sx={{ flex: 1, p: 3 }}>
          <TextField
            fullWidth
            label="Buscar serviço"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(1);
            }}
            sx={{ mb: 2 }}
          />

          {servicesQuery.isError ? (
            <Alert severity="error" sx={{ mb: 2 }}>
              {extractApiErrorMessage(
                servicesQuery.error,
                'Falha ao carregar serviços para composição.',
              )}
            </Alert>
          ) : null}

          <DataTable
            columns={[
              { key: 'codigo', header: 'Código', render: (row) => row.codigo_origem },
              { key: 'descricao', header: 'Descrição', render: (row) => row.descricao },
              { key: 'unidade', header: 'Unidade', render: (row) => row.unidade_medida },
              {
                key: 'custo',
                header: 'Custo',
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
            emptyTitle="Nenhum serviço disponível"
            emptyDescription="A composição só pode ser aberta para itens retornados pelo catálogo visível."
            onPageChange={setPage}
            onPageSizeChange={(value) => {
              setPageSize(value);
              setPage(1);
            }}
            onRowClick={(row) => setSelectedService(row)}
          />
        </Paper>

        <Stack spacing={2} sx={{ flex: 0.9 }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 1.5 }}>
              Explosão da composição
            </Typography>
            {selectedService ? (
              compositionQuery.data ? (
                <Stack spacing={1.5}>
                  <Typography variant="subtitle1">{selectedService.descricao}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Custo total da composição:{' '}
                    {formatCurrency(compositionQuery.data.custo_total_composicao)}
                  </Typography>
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
                    <Typography variant="body2" color="text.secondary">
                      Este item não possui componentes cadastrados.
                    </Typography>
                  )}
                </Stack>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Selecione um serviço para carregar a composição.
                </Typography>
              )
            ) : (
              <Typography variant="body2" color="text.secondary">
                Escolha um serviço na lista para visualizar os componentes.
              </Typography>
            )}
          </Paper>

          <ContractNotice
            title="Composição por cópia ainda depende de novas rotas"
            description="O backend já possui lógica de domínio para composição e anti-loop, mas ainda não publicou endpoints para criar, copiar, editar ou remover componentes via frontend."
            missingContracts={[
              'POST /composicoes/copia',
              'POST /composicoes/{paiId}/itens',
              'DELETE /composicoes/{paiId}/itens/{itemId}',
            ]}
            availableNow={[
              'GET /servicos/{id}/composicao',
              'GET /servicos/',
            ]}
          />
        </Stack>
      </Stack>
    </>
  );
}
