import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import { Button, Paper, Stack, Alert } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '../../auth/AuthProvider';
import { PageHeader } from '../../../shared/components/PageHeader';
import { EmptyState } from '../../../shared/components/EmptyState';
import { proposalsApi } from '../../../shared/services/api/proposalsApi';
import { extractApiErrorMessage } from '../../../shared/services/api/apiClient';
import { ProposalsTable } from '../components/ProposalsTable';

export function ProposalsListPage() {
  const navigate = useNavigate();
  const { selectedClientId, user } = useAuth();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['propostas', selectedClientId, page, pageSize],
    queryFn: () => proposalsApi.list(selectedClientId, page, pageSize),
    enabled: Boolean(selectedClientId),
  });

  if (!selectedClientId && !user?.is_admin) {
    return (
      <>
        <PageHeader title="Orçamentos" description="Gerencie suas propostas comerciais." />
        <EmptyState
          title="Selecione um cliente para ver as propostas"
          description="Utilize o seletor no topo da página para escolher um cliente e carregar seus dados."
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Orçamentos"
        description="Gerencie propostas comerciais, importe planilhas quantitativas e gere CPUs."
        actions={
          <Button
            variant="contained"
            startIcon={<AddOutlinedIcon />}
            onClick={() => navigate('/propostas/nova')}
            disabled={!selectedClientId}
          >
            Nova Proposta
          </Button>
        }
      />

      <Stack spacing={2}>
        {isError ? (
          <Alert severity="error">
            {extractApiErrorMessage(error, 'Falha ao carregar propostas.')}
          </Alert>
        ) : null}

        <Paper sx={{ p: 0 }}>
          <ProposalsTable
            propostas={data?.items ?? []}
            isLoading={isLoading}
            page={page}
            pageSize={pageSize}
            total={data?.total ?? 0}
            onPageChange={setPage}
            onPageSizeChange={(size) => {
              setPageSize(size);
              setPage(1);
            }}
          />
        </Paper>
      </Stack>
    </>
  );
}
