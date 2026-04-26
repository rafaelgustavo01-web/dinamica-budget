import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Paper, Stack, Typography, Button, Alert, Divider, Box } from '@mui/material';
import FileUploadOutlinedIcon from '@mui/icons-material/FileUploadOutlined';
import RuleOutlinedIcon from '@mui/icons-material/RuleOutlined';
import TableChartOutlinedIcon from '@mui/icons-material/TableChartOutlined';
import ShareIcon from '@mui/icons-material/Share';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';

import { PageHeader } from '../../../shared/components/PageHeader';
import { proposalsApi } from '../../../shared/services/api/proposalsApi';
import { StatusBadge } from '../../../shared/components/StatusBadge';
import { ExportMenu } from '../components/ExportMenu';
import { formatCurrency, formatDateTime } from '../../../shared/utils/format';
import { extractApiErrorMessage } from '../../../shared/services/api/apiClient';
import { useAuth } from '../../auth/AuthProvider';
import { ProposalShareDialog } from '../components/ProposalShareDialog';

export function ProposalDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { user } = useAuth();
  const [shareOpen, setShareOpen] = useState(false);

  const { data: proposta, isLoading, isError, error } = useQuery({
    queryKey: ['proposta', id],
    queryFn: () => proposalsApi.getById(id!),
    enabled: Boolean(id),
  });

  if (isLoading) return <Typography>Carregando...</Typography>;
  if (isError) return <Alert severity="error">{extractApiErrorMessage(error)}</Alert>;
  if (!proposta) return <Alert severity="warning">Proposta não encontrada.</Alert>;

  const isOwner = proposta.meu_papel === 'OWNER' || user?.is_admin;
  const canEdit = proposta.meu_papel === 'OWNER' || proposta.meu_papel === 'EDITOR' || user?.is_admin;

  return (
    <>
      <PageHeader
        title={`Proposta: ${proposta.codigo}`}
        description={proposta.titulo || 'Sem título'}
        actions={
          <Stack direction="row" spacing={1}>
            {isOwner && (
              <Button
                variant="outlined"
                startIcon={<ShareIcon />}
                onClick={() => setShareOpen(true)}
              >
                Compartilhar
              </Button>
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
      </Stack>
      {isOwner && <ProposalShareDialog propostaId={id!} open={shareOpen} onClose={() => setShareOpen(false)} />}
    </>
  );
}
