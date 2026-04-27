import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Paper,
  Stack,
  Typography,
  Button,
  Alert,
  Divider,
  Box,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import FileUploadOutlinedIcon from '@mui/icons-material/FileUploadOutlined';
import RuleOutlinedIcon from '@mui/icons-material/RuleOutlined';
import TableChartOutlinedIcon from '@mui/icons-material/TableChartOutlined';
import ShareIcon from '@mui/icons-material/Share';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import SendIcon from '@mui/icons-material/Send';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import HistoryIcon from '@mui/icons-material/History';

import { PageHeader } from '../../../shared/components/PageHeader';
import { proposalsApi } from '../../../shared/services/api/proposalsApi';
import { StatusBadge } from '../../../shared/components/StatusBadge';
import { ExportMenu } from '../components/ExportMenu';
import { ProposalHistoryPanel } from '../components/ProposalHistoryPanel';
import { formatCurrency, formatDateTime } from '../../../shared/utils/format';
import { extractApiErrorMessage } from '../../../shared/services/api/apiClient';
import { useAuth } from '../../auth/AuthProvider';
import { ProposalShareDialog } from '../components/ProposalShareDialog';

export function ProposalDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { user } = useAuth();
  const [shareOpen, setShareOpen] = useState(false);

  const { data: proposta, isLoading, isError, error } = useQuery({
    queryKey: ['proposta', id],
    queryFn: () => proposalsApi.getById(id!),
    enabled: Boolean(id),
  });

  const novaVersaoMutation = useMutation({
    mutationFn: () => proposalsApi.novaVersao(id!),
    onSuccess: (nova) => {
      queryClient.invalidateQueries({ queryKey: ['proposta', id] });
      navigate(`/propostas/${nova.id}`);
    },
  });

  const enviarAprovacaoMutation = useMutation({
    mutationFn: () => proposalsApi.enviarAprovacao(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposta', id] });
    },
  });

  const aprovarMutation = useMutation({
    mutationFn: () => proposalsApi.aprovar(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposta', id] });
    },
  });

  const rejeitarMutation = useMutation({
    mutationFn: () => proposalsApi.rejeitar(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proposta', id] });
    },
  });

  if (isLoading) return <Typography>Carregando...</Typography>;
  if (isError) return <Alert severity="error">{extractApiErrorMessage(error)}</Alert>;
  if (!proposta) return <Alert severity="warning">Proposta não encontrada.</Alert>;

  const isOwner = proposta.meu_papel === 'OWNER' || user?.is_admin;
  const canEdit = proposta.meu_papel === 'OWNER' || proposta.meu_papel === 'EDITOR' || user?.is_admin;
  const canApprove = proposta.meu_papel === 'APROVADOR' || proposta.meu_papel === 'OWNER' || user?.is_admin;

  const isCurrent = proposta.is_versao_atual !== false;
  const isClosed = proposta.is_fechada === true;

  // Approval workflow buttons
  const showNovaVersao = canEdit && isCurrent && !isClosed;
  const showEnviarAprovacao =
    canEdit &&
    proposta.requer_aprovacao &&
    proposta.status === 'CPU_GERADA' &&
    isCurrent &&
    !isClosed;
  const showAprovarRejeitar =
    canApprove && proposta.status === 'AGUARDANDO_APROVACAO';

  return (
    <>
      <PageHeader
        title={`Proposta: ${proposta.codigo}`}
        description={proposta.titulo || 'Sem título'}
        actions={
          <Stack direction="row" spacing={1} flexWrap="wrap">
            {isOwner && (
              <Button
                variant="outlined"
                startIcon={<ShareIcon />}
                onClick={() => setShareOpen(true)}
              >
                Compartilhar
              </Button>
            )}

            {showNovaVersao && (
              <Button
                variant="outlined"
                startIcon={<AddCircleOutlineIcon />}
                onClick={() => novaVersaoMutation.mutate()}
                disabled={novaVersaoMutation.isPending}
              >
                Nova Versão
              </Button>
            )}

            {showEnviarAprovacao && (
              <Button
                variant="contained"
                color="warning"
                startIcon={<SendIcon />}
                onClick={() => enviarAprovacaoMutation.mutate()}
                disabled={enviarAprovacaoMutation.isPending}
              >
                Enviar para Aprovação
              </Button>
            )}

            {showAprovarRejeitar && (
              <>
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<CheckCircleOutlineIcon />}
                  onClick={() => aprovarMutation.mutate()}
                  disabled={aprovarMutation.isPending}
                >
                  Aprovar
                </Button>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<CancelOutlinedIcon />}
                  onClick={() => rejeitarMutation.mutate()}
                  disabled={rejeitarMutation.isPending}
                >
                  Rejeitar
                </Button>
              </>
            )}

            <ExportMenu propostaId={id!} propostaCodigo={proposta.codigo} disabled={proposta.status === 'RASCUNHO'} />

            {canEdit && (
              <Button
                variant="outlined"
                startIcon={<FileUploadOutlinedIcon />}
                onClick={() => navigate(`/propostas/${id}/importar`)}
              >
                Importar PQ
              </Button>
            )}
            <Button
              variant="outlined"
              color="secondary"
              startIcon={<RuleOutlinedIcon />}
              onClick={() => navigate(`/propostas/${id}/match-review`)}
              disabled={proposta.status === 'RASCUNHO'}
            >
              Revisar Match
            </Button>
            <Button
              variant="contained"
              startIcon={<TableChartOutlinedIcon />}
              onClick={() => navigate(`/propostas/${id}/cpu`)}
              disabled={proposta.status === 'RASCUNHO'}
            >
              Ver CPU
            </Button>
            {isOwner && (
              <Button
                variant="outlined"
                color="error"
                startIcon={<DeleteOutlineIcon />}
                onClick={() => { /* TODO: implementar delete */ }}
              >
                Excluir
              </Button>
            )}
          </Stack>
        }
      />

      <Stack spacing={3}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Dados da Proposta</Typography>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
              gap: 2,
              mt: 2,
            }}
          >
            <Box>
              <Typography variant="caption" color="text.secondary">Status</Typography>
              <Box sx={{ mt: 0.5 }}>
                <StatusBadge value={proposta.status} kind="proposta" />
              </Box>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Criada em</Typography>
              <Typography variant="body2" sx={{ mt: 0.5 }}>{formatDateTime(proposta.created_at)}</Typography>
            </Box>
            {proposta.numero_versao != null && (
              <Box>
                <Typography variant="caption" color="text.secondary">Versão</Typography>
                <Typography variant="body2" sx={{ mt: 0.5 }}>v{proposta.numero_versao}</Typography>
              </Box>
            )}
            <Box sx={{ gridColumn: { md: 'span 2' } }}>
              <Typography variant="caption" color="text.secondary">Descrição</Typography>
              <Typography variant="body2" sx={{ mt: 0.5 }}>{proposta.descricao || 'Nenhuma descrição fornecida.'}</Typography>
            </Box>
          </Box>

          <Divider sx={{ my: 3 }} />

          <Typography variant="h6" gutterBottom>Totais</Typography>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', md: '1fr 1fr 1fr' },
              gap: 2,
              mt: 2,
            }}
          >
            <Box>
              <Typography variant="caption" color="text.secondary">Total Direto</Typography>
              <Typography variant="h6">{formatCurrency(proposta.total_direto)}</Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Total Indireto</Typography>
              <Typography variant="h6">{formatCurrency(proposta.total_indireto)}</Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Total Geral</Typography>
              <Typography variant="h6" color="primary.main" sx={{ fontWeight: 'bold' }}>
                {formatCurrency(proposta.total_geral)}
              </Typography>
            </Box>
          </Box>
        </Paper>

        {/* Histórico de versões */}
        {proposta.proposta_root_id && (
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Stack direction="row" spacing={1} alignItems="center">
                <HistoryIcon fontSize="small" color="action" />
                <Typography variant="subtitle1">Histórico de Versões</Typography>
              </Stack>
            </AccordionSummary>
            <AccordionDetails>
              <ProposalHistoryPanel
                rootId={proposta.proposta_root_id}
                currentVersionId={id!}
              />
            </AccordionDetails>
          </Accordion>
        )}
      </Stack>

      {isOwner && <ProposalShareDialog propostaId={id!} open={shareOpen} onClose={() => setShareOpen(false)} />}
    </>
  );
}
