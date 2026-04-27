import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Skeleton,
  Alert,
} from '@mui/material';

import { proposalsApi } from '../../../shared/services/api/proposalsApi';
import { StatusBadge } from '../../../shared/components/StatusBadge';
import { formatDateTime } from '../../../shared/utils/format';

interface ProposalHistoryPanelProps {
  rootId: string;
  currentVersionId: string;
}

export function ProposalHistoryPanel({ rootId, currentVersionId }: ProposalHistoryPanelProps) {
  const navigate = useNavigate();

  const { data: versoes, isLoading, isError } = useQuery({
    queryKey: ['proposta-versoes', rootId],
    queryFn: () => proposalsApi.listarVersoes(rootId),
    enabled: Boolean(rootId),
  });

  if (isLoading) {
    return (
      <Box sx={{ mt: 2 }}>
        <Skeleton height={40} />
        <Skeleton height={40} />
      </Box>
    );
  }

  if (isError) {
    return <Alert severity="error">Erro ao carregar histórico de versões.</Alert>;
  }

  if (!versoes || versoes.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        Nenhuma versão anterior encontrada.
      </Typography>
    );
  }

  return (
    <TableContainer>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Versão</TableCell>
            <TableCell>Código</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Criada em</TableCell>
            <TableCell>Atual</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {versoes.map((v) => (
            <TableRow
              key={v.id}
              hover
              sx={{ cursor: 'pointer' }}
              onClick={() => navigate(`/propostas/${v.id}`)}
              selected={v.id === currentVersionId}
            >
              <TableCell>
                <Typography variant="body2" fontWeight={v.id === currentVersionId ? 700 : 400}>
                  v{v.numero_versao}
                </Typography>
              </TableCell>
              <TableCell>{v.codigo}</TableCell>
              <TableCell>
                <StatusBadge value={v.status} kind="proposta" />
              </TableCell>
              <TableCell>{formatDateTime(v.created_at)}</TableCell>
              <TableCell>
                {v.is_versao_atual && (
                  <Chip label="Atual" size="small" color="primary" variant="outlined" />
                )}
                {v.is_fechada && !v.is_versao_atual && (
                  <Chip label="Fechada" size="small" color="default" variant="outlined" />
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
