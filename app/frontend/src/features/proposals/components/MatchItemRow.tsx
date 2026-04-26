import { useState } from 'react';
import {
  Button,
  Chip,
  Stack,
  TableCell,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined';
import SwapHorizOutlinedIcon from '@mui/icons-material/SwapHorizOutlined';
import type { PqItemResponse } from '../../../shared/services/api/proposalsApi';
import { ServicoPickerDialog } from './ServicoPickerDialog';

interface MatchItemRowProps {
  item: PqItemResponse;
  clienteId: string;
  onConfirmar: (itemId: string) => void;
  onRejeitar: (itemId: string) => void;
  onSubstituir: (itemId: string, servicoId: string, tipo: string) => void;
  isLoading: boolean;
}

const STATUS_LABELS: Record<string, { label: string; color: 'success' | 'warning' | 'error' | 'default' | 'info' }> = {
  SUGERIDO: { label: 'Sugerido', color: 'warning' },
  CONFIRMADO: { label: 'Confirmado', color: 'success' },
  MANUAL: { label: 'Manual', color: 'info' },
  SEM_MATCH: { label: 'Sem Match', color: 'error' },
  PENDENTE: { label: 'Pendente', color: 'default' },
  BUSCANDO: { label: 'Buscando', color: 'default' },
};

export function MatchItemRow({
  item,
  clienteId,
  onConfirmar,
  onRejeitar,
  onSubstituir,
  isLoading,
}: MatchItemRowProps) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const status = STATUS_LABELS[item.match_status] ?? { label: item.match_status, color: 'default' as const };
  const confianca = item.match_confidence
    ? `${(parseFloat(item.match_confidence) * 100).toFixed(0)}%`
    : '—';

  const podeAgir = item.match_status === 'SUGERIDO' || item.match_status === 'PENDENTE';

  return (
    <>
      <TableRow hover sx={{ opacity: isLoading ? 0.5 : 1 }}>
        <TableCell sx={{ width: 50 }}>
          <Typography variant="caption" color="text.secondary">
            {item.linha_planilha ?? '—'}
          </Typography>
        </TableCell>
        <TableCell sx={{ maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          <Tooltip title={item.codigo_original ?? ''}>
            <span>{item.codigo_original ?? '—'}</span>
          </Tooltip>
        </TableCell>
        <TableCell sx={{ maxWidth: 260 }}>
          <Tooltip title={item.descricao_original}>
            <Typography variant="body2" noWrap>{item.descricao_original}</Typography>
          </Tooltip>
        </TableCell>
        <TableCell sx={{ width: 60 }}>
          <Typography variant="body2">{item.unidade_medida_original ?? '—'}</Typography>
        </TableCell>
        <TableCell sx={{ width: 80 }}>
          <Typography variant="body2">{item.quantidade_original ?? '—'}</Typography>
        </TableCell>
        <TableCell sx={{ width: 80 }}>
          <Typography
            variant="body2"
            color={parseFloat(item.match_confidence ?? '0') >= 0.8 ? 'success.main' : 'warning.main'}
          >
            {confianca}
          </Typography>
        </TableCell>
        <TableCell sx={{ width: 120 }}>
          <Chip label={status.label} color={status.color} size="small" />
        </TableCell>
        <TableCell sx={{ width: 220 }}>
          {podeAgir && (
            <Stack direction="row" spacing={0.5}>
              <Tooltip title="Confirmar sugestão">
                <span>
                  <Button
                    size="small"
                    color="success"
                    onClick={() => onConfirmar(item.id)}
                    disabled={isLoading}
                    sx={{ minWidth: 0, px: 1 }}
                  >
                    <CheckCircleOutlineIcon fontSize="small" />
                  </Button>
                </span>
              </Tooltip>
              <Tooltip title="Substituir por outro serviço">
                <span>
                  <Button
                    size="small"
                    color="info"
                    onClick={() => setPickerOpen(true)}
                    disabled={isLoading}
                    sx={{ minWidth: 0, px: 1 }}
                  >
                    <SwapHorizOutlinedIcon fontSize="small" />
                  </Button>
                </span>
              </Tooltip>
              <Tooltip title="Rejeitar (sem match)">
                <span>
                  <Button
                    size="small"
                    color="error"
                    onClick={() => onRejeitar(item.id)}
                    disabled={isLoading}
                    sx={{ minWidth: 0, px: 1 }}
                  >
                    <CancelOutlinedIcon fontSize="small" />
                  </Button>
                </span>
              </Tooltip>
            </Stack>
          )}
        </TableCell>
      </TableRow>

      <ServicoPickerDialog
        open={pickerOpen}
        clienteId={clienteId}
        descricaoOriginal={item.descricao_original}
        onSelect={(servicoId, tipo) => onSubstituir(item.id, servicoId, tipo)}
        onClose={() => setPickerOpen(false)}
      />
    </>
  );
}
