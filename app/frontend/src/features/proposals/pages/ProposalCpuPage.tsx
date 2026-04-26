import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  InputAdornment,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import ArrowBackOutlinedIcon from '@mui/icons-material/ArrowBackOutlined';
import CalculateOutlinedIcon from '@mui/icons-material/CalculateOutlined';
import PlayArrowOutlinedIcon from '@mui/icons-material/PlayArrowOutlined';

import { PageHeader } from '../../../shared/components/PageHeader';
import { proposalsApi } from '../../../shared/services/api/proposalsApi';
import { extractApiErrorMessage } from '../../../shared/services/api/apiClient';
import { formatCurrency } from '../../../shared/utils/format';
import { CpuTable } from '../components/CpuTable';

export function ProposalCpuPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [bdi, setBdi] = useState('25');

  const { data: proposta } = useQuery({
    queryKey: ['proposta', id],
    queryFn: () => proposalsApi.getById(id!),
    enabled: Boolean(id),
  });

  const { data: itens = [], isLoading: loadingItens } = useQuery({
    queryKey: ['cpu-itens', id],
    queryFn: () => proposalsApi.listCpuItens(id!),
    enabled: Boolean(id),
  });

  const gerarMutation = useMutation({
    mutationFn: () =>
      proposalsApi.gerarCpu(id!, parseFloat(bdi) || 0),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['cpu-itens', id] });
      void queryClient.invalidateQueries({ queryKey: ['proposta', id] });
    },
  });

  const recalcularMutation = useMutation({
    mutationFn: () =>
      proposalsApi.recalcularBdi(id!, { percentual_bdi: parseFloat(bdi) || 0 }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['cpu-itens', id] });
      void queryClient.invalidateQueries({ queryKey: ['proposta', id] });
    },
  });

  const jaTemItens = itens.length > 0;

  return (
    <>
      <PageHeader
        title="Visualização de CPU"
        description={`Proposta ${proposta?.codigo ?? ''} — ${itens.length} itens`}
        actions={
          <Button
            variant="outlined"
            startIcon={<ArrowBackOutlinedIcon />}
            onClick={() => navigate(`/propostas/${id}`)}
          >
            Voltar
          </Button>
        }
      />

      <Stack spacing={3}>
        {(gerarMutation.isError || recalcularMutation.isError) && (
          <Alert severity="error">
            {extractApiErrorMessage(gerarMutation.error ?? recalcularMutation.error)}
          </Alert>
        )}

        <Paper sx={{ p: 3 }}>
          <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
            <TextField
              label="BDI (%)"
              type="number"
              value={bdi}
              onChange={(e) => setBdi(e.target.value)}
              InputProps={{
                endAdornment: <InputAdornment position="end">%</InputAdornment>,
              }}
              inputProps={{ min: 0, max: 100, step: 0.5 }}
              sx={{ width: 150 }}
            />
            {!jaTemItens ? (
              <Button
                variant="contained"
                startIcon={<PlayArrowOutlinedIcon />}
                onClick={() => gerarMutation.mutate()}
                disabled={gerarMutation.isPending}
              >
                {gerarMutation.isPending ? 'Gerando CPU...' : 'Gerar CPU'}
              </Button>
            ) : (
              <Button
                variant="outlined"
                startIcon={<CalculateOutlinedIcon />}
                onClick={() => recalcularMutation.mutate()}
                disabled={recalcularMutation.isPending}
              >
                {recalcularMutation.isPending ? 'Recalculando...' : 'Recalcular BDI'}
              </Button>
            )}

            {proposta && (
              <Stack direction="row" spacing={2} sx={{ ml: 'auto' }}>
                <Box textAlign="right">
                  <Typography variant="caption" color="text.secondary">Total Direto</Typography>
                  <Typography variant="h6">{formatCurrency(proposta.total_direto ?? 0)}</Typography>
                </Box>
                <Box textAlign="right">
                  <Typography variant="caption" color="text.secondary">Total Indireto (BDI)</Typography>
                  <Typography variant="h6">{formatCurrency(proposta.total_indireto ?? 0)}</Typography>
                </Box>
                <Box textAlign="right">
                  <Typography variant="caption" color="text.secondary">Total Geral</Typography>
                  <Typography variant="h6" color="primary.main" fontWeight="bold">
                    {formatCurrency(proposta.total_geral ?? 0)}
                  </Typography>
                </Box>
              </Stack>
            )}
          </Stack>

          {gerarMutation.isSuccess && (
            <Alert severity="success" sx={{ mt: 2 }}>
              CPU gerada com sucesso: {gerarMutation.data.detalhe.processados} itens processados,{' '}
              {gerarMutation.data.detalhe.erros} erros.
            </Alert>
          )}
          {recalcularMutation.isSuccess && (
            <Alert severity="success" sx={{ mt: 2 }}>
              BDI recalculado: {recalcularMutation.data.itens_recalculados} itens atualizados.
            </Alert>
          )}
        </Paper>

        <Paper>
          {loadingItens ? (
            <Box sx={{ p: 3 }}>
              <Typography>Carregando itens...</Typography>
            </Box>
          ) : (
            <CpuTable itens={itens} propostaId={id!} />
          )}
        </Paper>
      </Stack>
    </>
  );
}
