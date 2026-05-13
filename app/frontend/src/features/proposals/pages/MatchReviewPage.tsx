import { useCallback, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useVirtualizer } from '@tanstack/react-virtual';
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
import DoneAllOutlinedIcon from '@mui/icons-material/DoneAllOutlined';

import { PageHeader } from '../../../shared/components/PageHeader';
import { proposalsApi } from '../../../shared/services/api/proposalsApi';
import type { PqItemResponse, TipoServicoMatch } from '../../../shared/services/api/proposalsApi';
import { extractApiErrorMessage } from '../../../shared/services/api/apiClient';
import { MatchItemRow } from '../components/MatchItemRow';

const PQ_ITENS_KEY = (id: string) => ['pq-itens', id];

export function MatchReviewPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const tableContainerRef = useRef<HTMLDivElement>(null);
  const [pendingIds, setPendingIds] = useState<Set<string>>(new Set());

  const { data: proposta } = useQuery({
    queryKey: ['proposta', id],
    queryFn: () => proposalsApi.getById(id!),
    enabled: Boolean(id),
  });

  const { data: itens = [], isLoading, isError, error } = useQuery({
    queryKey: PQ_ITENS_KEY(id!),
    queryFn: () => proposalsApi.listPqItens(id!),
    enabled: Boolean(id),
  });

  const applyPatch = useCallback(
    (itemId: string, patch: Partial<PqItemResponse>) => {
      queryClient.setQueryData<PqItemResponse[]>(PQ_ITENS_KEY(id!), (old) =>
        old?.map((item) => (item.id === itemId ? { ...item, ...patch } : item)),
      );
    },
    [id, queryClient],
  );

  const addPending = useCallback((itemId: string) => {
    setPendingIds((prev) => new Set(prev).add(itemId));
  }, []);

  const removePending = useCallback((itemId: string) => {
    setPendingIds((prev) => {
      const next = new Set(prev);
      next.delete(itemId);
      return next;
    });
  }, []);

  const confirmarMutation = useMutation({
    mutationFn: (itemId: string) =>
      proposalsApi.confirmarMatch(id!, itemId, { acao: 'confirmar' }),
    onMutate: (itemId) => {
      addPending(itemId);
      applyPatch(itemId, { match_status: 'CONFIRMADO' });
    },
    onError: (_err, itemId) => applyPatch(itemId, { match_status: 'SUGERIDO' }),
    onSettled: (_data, _err, itemId) => removePending(itemId),
  });

  const rejeitarMutation = useMutation({
    mutationFn: (itemId: string) =>
      proposalsApi.confirmarMatch(id!, itemId, { acao: 'rejeitar' }),
    onMutate: (itemId) => {
      addPending(itemId);
      applyPatch(itemId, { match_status: 'SEM_MATCH' });
    },
    onError: (_err, itemId) => applyPatch(itemId, { match_status: 'SUGERIDO' }),
    onSettled: (_data, _err, itemId) => removePending(itemId),
  });

  const substituirMutation = useMutation({
    mutationFn: ({ itemId, servicoId, tipo }: { itemId: string; servicoId: string; tipo: TipoServicoMatch }) =>
      proposalsApi.confirmarMatch(id!, itemId, {
        acao: 'substituir',
        servico_match_id: servicoId,
        servico_match_tipo: tipo,
      }),
    onMutate: ({ itemId, servicoId, tipo }) => {
      addPending(itemId);
      applyPatch(itemId, { match_status: 'MANUAL', servico_match_id: servicoId, servico_match_tipo: tipo });
    },
    onError: (_err, { itemId }) => applyPatch(itemId, { match_status: 'SUGERIDO' }),
    onSettled: (_data, _err, { itemId }) => removePending(itemId),
  });

  const confirmarTodosMutation = useMutation({
    mutationFn: () => proposalsApi.confirmarTodosSugeridos(id!),
    onSuccess: (_data) => {
      // Patch cache: all SUGERIDO → CONFIRMADO
      queryClient.setQueryData<PqItemResponse[]>(PQ_ITENS_KEY(id!), (old) =>
        old?.map((item) =>
          item.match_status === 'SUGERIDO' ? { ...item, match_status: 'CONFIRMADO' } : item,
        ),
      );
    },
  });

  const rowVirtualizer = useVirtualizer({
    count: itens.length,
    getScrollElement: () => tableContainerRef.current,
    estimateSize: () => 45,
    overscan: 15,
  });

  const confirmados = itens.filter(
    (i) => i.match_status === 'CONFIRMADO' || i.match_status === 'MANUAL',
  ).length;
  const rejeitados = itens.filter((i) => i.match_status === 'SEM_MATCH').length;
  const progresso = itens.length > 0 ? ((confirmados + rejeitados) / itens.length) * 100 : 0;
  const hasError = confirmarMutation.isError || rejeitarMutation.isError || substituirMutation.isError;

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
              variant="outlined"
              color="success"
              startIcon={<DoneAllOutlinedIcon />}
              loading={confirmarTodosMutation.isPending}
              onClick={() => confirmarTodosMutation.mutate()}
            >
              Confirmar Todos Sugeridos
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

        {hasError && (
          <Alert severity="error">
            {extractApiErrorMessage(
              confirmarMutation.error ?? rejeitarMutation.error ?? substituirMutation.error,
            )}
          </Alert>
        )}

        <Paper>
          <TableContainer
            ref={tableContainerRef}
            sx={{ height: 560, overflowY: 'auto', overflowX: 'auto' }}
          >
            {isLoading ? (
              <Box sx={{ p: 3 }}>
                <LinearProgress />
              </Box>
            ) : itens.length === 0 ? (
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <Typography color="text.secondary">
                  Nenhum item importado. Execute a importação primeiro.
                </Typography>
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
                <TableBody
                  sx={{
                    height: `${rowVirtualizer.getTotalSize()}px`,
                    position: 'relative',
                  }}
                >
                  {rowVirtualizer.getVirtualItems().map((virtualRow) => {
                    const item = itens[virtualRow.index];
                    return (
                      <MatchItemRow
                        key={item.id}
                        item={item}
                        clienteId={proposta?.cliente_id ?? ''}
                        isLoading={pendingIds.has(item.id)}
                        virtualStyle={{
                          position: 'absolute',
                          top: 0,
                          left: 0,
                          width: '100%',
                          height: `${virtualRow.size}px`,
                          transform: `translateY(${virtualRow.start}px)`,
                        }}
                        onConfirmar={(itemId) => confirmarMutation.mutate(itemId)}
                        onRejeitar={(itemId) => rejeitarMutation.mutate(itemId)}
                        onSubstituir={(itemId, servicoId, tipo) =>
                          substituirMutation.mutate({ itemId, servicoId, tipo: tipo as TipoServicoMatch })
                        }
                      />
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </TableContainer>
        </Paper>
      </Stack>
    </>
  );
}
