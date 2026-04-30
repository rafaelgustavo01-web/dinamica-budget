import { Paper, Stack, Alert } from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '../../auth/AuthProvider';
import { PageHeader } from '../../../shared/components/PageHeader';
import { EmptyState } from '../../../shared/components/EmptyState';
import { proposalsApi } from '../../../shared/services/api/proposalsApi';
import { extractApiErrorMessage } from '../../../shared/services/api/apiClient';
import { ProposalForm } from '../components/ProposalForm';
import type { PropostaFormData } from '../types';

export function ProposalCreatePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { selectedClientId } = useAuth();

  const mutation = useMutation({
    mutationFn: (data: PropostaFormData) =>
      proposalsApi.create({
        cliente_id: selectedClientId,
        ...data,
      }),
    onSuccess: (newProposta) => {
      void queryClient.invalidateQueries({ queryKey: ['propostas', selectedClientId] });
      navigate(`/propostas/${newProposta.id}`);
    },
  });

  if (!selectedClientId) {
    return (
      <>
        <PageHeader
          title="Nova Proposta"
          description="Crie um rascunho de proposta comercial para iniciar a orçamentação."
        />
        <EmptyState
          title="Selecione um cliente para criar uma proposta"
          description="Defina o cliente no topo da tela antes de iniciar a orçamentação."
          actionLabel="Voltar para Orçamentos"
          onAction={() => navigate('/propostas')}
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Nova Proposta"
        description="Crie um rascunho de proposta comercial para iniciar a orçamentação."
      />

      <Stack spacing={2}>
        {mutation.isError ? (
          <Alert severity="error">
            {extractApiErrorMessage(mutation.error, 'Falha ao criar proposta.')}
          </Alert>
        ) : null}

        <Paper sx={{ p: 3 }}>
          <ProposalForm
            onSubmit={(data) => mutation.mutate(data)}
            isLoading={mutation.isPending}
            onCancel={() => navigate('/propostas')}
          />
        </Paper>
      </Stack>
    </>
  );
}
