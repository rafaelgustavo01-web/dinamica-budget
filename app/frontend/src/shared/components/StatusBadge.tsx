import { Chip, useTheme } from '@mui/material';

import { statusColors } from '../../app/theme/tokens';
import { getHomologacaoLabel, getOrigemMatchLabel, getPropostaStatusLabel } from '../utils/format';

interface StatusBadgeProps {
  value: string;
  kind?: 'status' | 'origemMatch' | 'proposta';
}

function normalizeStatusKey(value: string, kind: 'status' | 'origemMatch' | 'proposta') {
  if (!value) {
    return 'tcpo';
  }

  const normalized = String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase();

  if (kind === 'origemMatch') {
    if (normalized === 'PROPRIA_CLIENTE') {
      return 'propria';
    }

    return 'tcpo';
  }

  if (['APROVADO', 'VALIDADA', 'CONSOLIDADA', 'APROVADA', 'CPU_GERADA'].includes(normalized)) {
    return 'aprovado';
  }

  if (['PENDENTE', 'SUGERIDA', 'EM_ANALISE', 'AGUARDANDO_APROVACAO'].includes(normalized)) {
    return 'pendente';
  }

  if (['REPROVADO', 'REJEITADO', 'REPROVADA'].includes(normalized)) {
    return 'rejeitado';
  }

  if (normalized === 'ATIVO') {
    return 'ativo';
  }

  if (normalized === 'INATIVO' || normalized === 'ARQUIVADA') {
    return 'inativo';
  }

  if (normalized === 'RASCUNHO') {
    return 'rascunho';
  }

  if (normalized === 'EM_REVISAO') {
    return 'em-revisao';
  }

  if (normalized === 'TCPO') {
    return 'tcpo';
  }

  if (normalized === 'PROPRIA') {
    return 'propria';
  }

  return 'tcpo';
}

export function StatusBadge({ value, kind = 'status' }: StatusBadgeProps) {
  const theme = useTheme();
  const paletteByMode = theme.palette.mode === 'light' ? statusColors.light : statusColors.dark;
  const colorKey = normalizeStatusKey(value, kind);
  const colorSet = paletteByMode[colorKey];
  
  const getLabel = () => {
    if (kind === 'origemMatch') return getOrigemMatchLabel(value as never);
    if (kind === 'proposta') return getPropostaStatusLabel(value);
    return getHomologacaoLabel(value);
  };

  return (
    <Chip
      size="small"
      label={getLabel()}
      sx={{
        color: colorSet.color,
        backgroundColor: colorSet.bg,
        border: 'none',
      }}
    />
  );
}

