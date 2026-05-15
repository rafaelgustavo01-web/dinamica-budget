import { memo, useState } from 'react';
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
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import SwapHorizOutlinedIcon from '@mui/icons-material/SwapHorizOutlined';
import type { PqItemResponse } from '../../../shared/services/api/proposalsApi';
import { formatQuantity, formatUnit, formatPercent } from '../../../shared/utils/format';
import { ServicoPickerDialog } from './ServicoPickerDialog';

interface MatchItemRowProps {
  item: PqItemResponse;
  clienteId: string;
  onConfirmar: (itemId: string) => void;
  onRejeitar: (itemId: string) => void;
  onSubstituir: (itemId: string, servicoId: string, tipo: string) => void;
  onDelete?: (itemId: string) => void;
  isLoading: boolean;
}

const STATUS_LABELS: Record<string, { label: string; color: 'success' | 'warning' | 'error' | 'default' | 'info' }> = {
  SUGERIDO: { label: 'Sugerido', color: 'info' },
  CONFIRMADO: { label: 'Confirmado', color: 'success' },
  MANUAL: { label: 'Manual', color: 'warning' },
  SEM_MATCH: { label: 'Sem Match', color: 'error' },
  PENDENTE: { label: 'Pendente', color: 'default' },
  BUSCANDO: { label: 'Buscando', color: 'default' },
};

function MatchItemRowInner({
  item,
  clienteId,
  onConfirmar,
  onRejeitar,
  onSubstituir,
  onDelete,
  isLoading,
}: MatchItemRowProps) {
  const [pickerOpen, setPickerOpen] = useState(false);
  const status = STATUS_LABELS[item.match_status] ?? { label: item.match_status, color: 'default' as const };
  const confiancaNum = item.match_confidence ? parseFloat(item.match_confidence) : 0;
  const confiancaColor = confiancaNum >= 0.85 ? 'success.main' : confiancaNum >= 0.65 ? 'warning.main' : 'error.main';

  const podeAgir = item.match_status === 'SUGERIDO' || item.match_status === 'PENDENTE' || item.match_status === 'SEM_MATCH';
  const suggestedLabel = item.servico_match_descricao
    ? `${item.servico_match_codigo ?? 'Sem código'} - ${item.servico_match_descricao}`
    : 'Sem sugestão';

  return (
    <>
      <TableRow hover sx={{ opacity: isLoading ? 0.5 : 1 }}>
        <TableCell sx={{ width: 70 }} align="center">
          <Typography variant="caption" color="text.secondary">
            {item.linha_planilha ?? '—'}
          </Typography>
        </TableCell>
        <TableCell sx={{ width: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          <Tooltip title={item.codigo_original ?? ''}>
            <span>{item.codigo_original ?? '—'}</span>
          </Tooltip>
        </TableCell>
        <TableCell>
          <Tooltip title={item.descricao_original}>
            <Typography
              variant="body2"
              sx={{
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }}
            >
              {item.descricao_original}
            </Typography>
          </Tooltip>
        </TableCell>
        <TableCell sx={{ minWidth: 260 }}>
          <Tooltip title={suggestedLabel}>
            <Typography variant="body2" noWrap sx={{ maxWidth: 340 }}>
              {suggestedLabel}
            </Typography>
          </Tooltip>
          {item.servico_match_unidade && (
            <Typography variant="caption" color="text.secondary">
              {formatUnit(item.servico_match_unidade)}
            </Typography>
          )}
        </TableCell>
        <TableCell sx={{ width: 70 }} align="center">
          <Typography variant="body2">{formatUnit(item.unidade_medida_original)}</Typography>
        </TableCell>
        <TableCell sx={{ width: 110 }} align="right">
          <Typography variant="body2" fontFamily="monospace">
            {formatQuantity(item.quantidade_original)}
          </Typography>
        </TableCell>
        <TableCell sx={{ width: 90 }} align="center">
          <Typography variant="body2" color={item.match_confidence ? confiancaColor : 'text.secondary'}>
            {formatPercent(item.match_confidence)}
          </Typography>
        </TableCell>
        <TableCell sx={{ width: 130 }}>
          <Chip label={status.label} color={status.color} size="small" />
        </TableCell>
        <TableCell sx={{ width: 130 }}>
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
              <Tooltip title="Marcar como sem correspondência">
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
              {onDelete && (
                <Tooltip title="Remover linha da PQ">
                  <span>
                    <Button size="small" color="error" onClick={() => onDelete(item.id)} disabled={isLoading} sx={{ minWidth: 0, px: 1 }}>
                      <DeleteOutlineIcon fontSize="small" />
                    </Button>
                  </span>
                </Tooltip>
              )}
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

export const MatchItemRow = memo(MatchItemRowInner);
