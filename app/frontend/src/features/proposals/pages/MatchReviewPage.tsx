import { useParams, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  LinearProgress,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import ArrowBackOutlinedIcon from '@mui/icons-material/ArrowBackOutlined';
import ChecklistOutlinedIcon from '@mui/icons-material/ChecklistOutlined';

import { PageHeader } from '../../../shared/components/PageHeader';
import { proposalsApi } from '../../../shared/services/api/proposalsApi';
import type { TipoServicoMatch } from '../../../shared/services/api/proposalsApi';
import { extractApiErrorMessage } from '../../../shared/services/api/apiClient';
import { MatchItemRow } from '../components/MatchItemRow';

export function MatchReviewPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: proposta } = useQuery({
    queryKey: ['proposta', id],
    queryFn: () => proposalsApi.getById(id!),
    enabled: Boolean(id),
  });

  const { data: itens = [], isLoading, isError, error } = useQuery({
    queryKey: ['pq-itens', id],
    queryFn: () => proposalsApi.listPqItens(id!),
    enabled: Boolean(id),
  });

  const confirmarMutation = useMutation({
    mutationFn: (itemId: string) =>
      proposalsApi.confirmarMatch(id!, itemId, { acao: 'confirmar' }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['pq-itens', id] }),
  });

  const rejeitarMutation = useMutation({
    mutationFn: (itemId: string) =>
      proposalsApi.confirmarMatch(id!, itemId, { acao: 'rejeitar' }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['pq-itens', id] }),
  });

  const substituirMutation = useMutation({
    mutationFn: ({
      itemId,
      servicoId,
      tipo,
    }: {
      itemId: string;
      servicoId: string;
      tipo: TipoServicoMatch;
    }) =>
      proposalsApi.confirmarMatch(id!, itemId, {
        acao: 'substituir',
        servico_match_id: servicoId,
        servico_match_tipo: tipo,
      }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['pq-itens', id] }),
  });

  const confirmados = itens.filter(
    (i) => i.match_status === 'CONFIRMADO' || i.match_status === 'MANUAL',
  ).length;
  const rejeitados = itens.filter((i) => i.match_status === 'SEM_MATCH').length;
  const progresso = itens.length > 0 ? ((confirmados + rejeitados) / itens.length) * 100 : 0;
  const isMutating =
    confirmarMutation.isPending ||
    rejeitarMutation.isPending ||
    substituirMutation.isPending;

  if (isError) return <Alert severity="error">{extractApiErrorMessage(error)}</Alert>;

  return (
    <>
      <PageHeader
        title="Revisão de Match"
        description={`Proposta ${proposta?.codigo ?? ''} — ${itens.length} itens`}
        actions={
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              startIcon={<ArrowBackOutlinedIcon />}
              onClick={() => navigate(`/propostas/${id}/importar`)}
            >
              Voltar
            </Button>
            <Button
              variant="contained"
              startIcon={<ChecklistOutlinedIcon />}
              disabled={confirmados + rejeitados === 0}
              onClick={() => navigate(`/propostas/${id}/cpu`)}
            >
              Ir para CPU ({confirmados} confirmados)
            </Button>
          </Stack>
        }
      />

      <Stack spacing={3}>
        <Paper sx={{ p: 2 }}>
          <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 1 }}>
            <Typography variant="body2">
              Revisados: <strong>{confirmados + rejeitados}</strong> de{' '}
              <strong>{itens.length}</strong>
            </Typography>
            <Typography variant="body2" color="success.main">
              ✓ {confirmados} confirmados
            </Typography>
            <Typography variant="body2" color="error.main">
              ✗ {rejeitados} rejeitados
            </Typography>
          </Stack>
          <LinearProgress variant="determinate" value={progresso} sx={{ height: 8, borderRadius: 4 }} />
        </Paper>

        {(confirmarMutation.isError || rejeitarMutation.isError || substituirMutation.isError) && (
          <Alert severity="error">
            {extractApiErrorMessage(
              confirmarMutation.error ?? rejeitarMutation.error ?? substituirMutation.error,
            )}
          </Alert>
        )}

        <TableContainer component={Paper} sx={{ overflowX: 'auto' }}>
          {isLoading ? (
            <Box sx={{ p: 3 }}>
              <LinearProgress />
            </Box>
          ) : (
            <Table size="small" sx={{ minWidth: 820 }}>
              <TableHead>
                <TableRow>
                  <TableCell>Linha</TableCell>
                  <TableCell>Código</TableCell>
                  <TableCell>Descrição Original</TableCell>
                  <TableCell>Unid.</TableCell>
                  <TableCell>Qtd</TableCell>
                  <TableCell>Conf.</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Ações</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {itens.map((item) => (
                  <MatchItemRow
                    key={item.id}
                    item={item}
                    clienteId={proposta?.cliente_id ?? ''}
                    isLoading={isMutating}
                    onConfirmar={(itemId) => confirmarMutation.mutate(itemId)}
                    onRejeitar={(itemId) => rejeitarMutation.mutate(itemId)}
                    onSubstituir={(itemId, servicoId, tipo) =>
                      substituirMutation.mutate({
                        itemId,
                        servicoId,
                        tipo: tipo as TipoServicoMatch,
                      })
                    }
                  />
                ))}
                {itens.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                      <Typography color="text.secondary">
                        Nenhum item importado. Execute a importação primeiro.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </TableContainer>
      </Stack>
    </>
  );
}
