import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import RefreshIcon from '@mui/icons-material/Refresh';
import { Alert, Box, Button, Card, CardContent, Chip, CircularProgress, Stack, Typography } from '@mui/material';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '../../../shared/components/PageHeader';
import { proposalsApi } from '../../../shared/services/api/proposalsApi';
import { ProposalItemsManager } from '../components/ProposalItemsManager';

export function ProposalItemsPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: proposta, isLoading, refetch } = useQuery({
    queryKey: ['proposta', id],
    queryFn: () => proposalsApi.getById(id!),
    enabled: Boolean(id),
  });

  const handleRefresh = () => {
    void refetch();
    if (id) {
      void queryClient.invalidateQueries({ queryKey: ['proposalItems', id] });
    }
  };

  if (!id) {
    return <Alert severity="error">Proposta não informada.</Alert>;
  }

  const canEdit = proposta?.status === 'RASCUNHO' || proposta?.status === 'CPU_GERADA';

  return (
    <>
      <PageHeader
        title={proposta ? 'Itens: ' + proposta.codigo : 'Itens da Proposta'}
        description={proposta?.titulo || ''}
        actions={
          <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
            <Button
              variant="outlined"
              startIcon={<ArrowBackIcon />}
              onClick={() => navigate('/propostas/' + id)}
            >
              Voltar
            </Button>
            <Button variant="outlined" startIcon={<RefreshIcon />} onClick={handleRefresh} disabled={isLoading}>
              Atualizar
            </Button>
          </Stack>
        }
      />

      <Stack spacing={3} sx={{ py: 3 }}>
        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {proposta && (
              <Card>
                <CardContent>
                  <Stack direction="row" spacing={2} alignItems="center">
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Status
                      </Typography>
                      <Typography variant="body2">{proposta.status}</Typography>
                    </Box>
                    {proposta.cpu_desatualizada && (
                      <Chip label="CPU Desatualizada" color="warning" size="small" />
                    )}
                  </Stack>
                </CardContent>
              </Card>
            )}

            {!canEdit && proposta && (
              <Alert severity="info">
                Itens podem ser adicionados apenas em status RASCUNHO ou CPU_GERADA. Status atual:{' '}
                <strong>{proposta.status}</strong>
              </Alert>
            )}

            <ProposalItemsManager
              propostaId={id}
              propostaStatus={proposta?.status ?? 'RASCUNHO'}
              userRole={proposta?.meu_papel ?? undefined}
            />
          </>
        )}
      </Stack>
    </>
  );
}
