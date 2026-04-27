import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Button,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
} from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined';

import { PageHeader } from '../../../shared/components/PageHeader';
import { proposalsApi, type PropostaResponse } from '../../../shared/services/api/proposalsApi';
import { StatusBadge } from '../../../shared/components/StatusBadge';
import { formatCurrency, formatDateTime } from '../../../shared/utils/format';
import { extractApiErrorMessage } from '../../../shared/services/api/apiClient';

export function ApprovalQueuePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [rejectTarget, setRejectTarget] = useState<PropostaResponse | null>(null);
  const [motivoRejeicao, setMotivoRejeicao] = useState('');

  const { data: propostas, isLoading, isError, error } = useQuery({
    queryKey: ['aprovacoes'],
    queryFn: () => proposalsApi.filaAprovacoes(),
  });

  const aprovarMutation = useMutation({
    mutationFn: (propostaId: string) => proposalsApi.aprovar(propostaId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aprovacoes'] });
    },
  });

  const rejeitarMutation = useMutation({
    mutationFn: ({ propostaId, motivo }: { propostaId: string; motivo?: string }) =>
      proposalsApi.rejeitar(propostaId, motivo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aprovacoes'] });
      setRejectTarget(null);
      setMotivoRejeicao('');
    },
  });

  const handleAprovar = (proposta: PropostaResponse) => {
    aprovarMutation.mutate(proposta.id);
  };

  const handleConfirmarRejeicao = () => {
    if (!rejectTarget) return;
    rejeitarMutation.mutate({ propostaId: rejectTarget.id, motivo: motivoRejeicao || undefined });
  };

  if (isLoading) return <Typography>Carregando...</Typography>;
  if (isError) return <Alert severity="error">{extractApiErrorMessage(error)}</Alert>;

  const isEmpty = !propostas || propostas.length === 0;

  return (
    <>
      <PageHeader
        title="Fila de Aprovação"
        description="Propostas aguardando sua aprovação"
      />

      {isEmpty ? (
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <CheckCircleOutlineIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            Nenhuma proposta aguardando aprovação
          </Typography>
          <Typography variant="body2" color="text.disabled" sx={{ mt: 1 }}>
            Quando propostas forem enviadas para aprovação, elas aparecerão aqui.
          </Typography>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Código</TableCell>
                <TableCell>Título</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Total Geral</TableCell>
                <TableCell>Criada em</TableCell>
                <TableCell align="right">Ações</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {propostas.map((p) => (
                <TableRow key={p.id} hover>
                  <TableCell>
                    <Typography
                      variant="body2"
                      sx={{ cursor: 'pointer', color: 'primary.main', fontWeight: 500 }}
                      onClick={() => navigate(`/propostas/${p.id}`)}
                    >
                      {p.codigo}
                    </Typography>
                  </TableCell>
                  <TableCell>{p.titulo || '-'}</TableCell>
                  <TableCell>
                    <StatusBadge value={p.status} kind="proposta" />
                  </TableCell>
                  <TableCell>{formatCurrency(p.total_geral)}</TableCell>
                  <TableCell>{formatDateTime(p.created_at)}</TableCell>
                  <TableCell align="right">
                    <Stack direction="row" spacing={1} justifyContent="flex-end">
                      <Button
                        size="small"
                        variant="contained"
                        color="success"
                        startIcon={<CheckCircleOutlineIcon />}
                        onClick={() => handleAprovar(p)}
                        disabled={aprovarMutation.isPending}
                      >
                        Aprovar
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        color="error"
                        startIcon={<CancelOutlinedIcon />}
                        onClick={() => {
                          setRejectTarget(p);
                          setMotivoRejeicao('');
                        }}
                        disabled={rejeitarMutation.isPending}
                      >
                        Rejeitar
                      </Button>
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Rejection dialog */}
      <Dialog
        open={Boolean(rejectTarget)}
        onClose={() => setRejectTarget(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Rejeitar proposta</DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            A proposta <strong>{rejectTarget?.codigo}</strong> voltará para o status CPU_GERADA.
            Informe o motivo da rejeição (opcional).
          </DialogContentText>
          <TextField
            autoFocus
            label="Motivo da rejeição"
            multiline
            rows={3}
            fullWidth
            value={motivoRejeicao}
            onChange={(e) => setMotivoRejeicao(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRejectTarget(null)}>Cancelar</Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleConfirmarRejeicao}
            disabled={rejeitarMutation.isPending}
          >
            Confirmar Rejeição
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
