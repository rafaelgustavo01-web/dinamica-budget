import { Chip, useTheme } from '@mui/material';

import { statusColors } from '../../app/theme/tokens';
import { getHomologacaoLabel, getOrigemMatchLabel } from '../utils/format';

interface StatusBadgeProps {
  value: string;
  kind?: 'status' | 'origemMatch';
}

function normalizeStatusKey(value: string, kind: 'status' | 'origemMatch') {
  const normalized = value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase();

  if (kind === 'origemMatch') {
    if (normalized === 'PROPRIA_CLIENTE') {
      return 'propria';
    }

    return 'tcpo';
  }

  if (['APROVADO', 'VALIDADA', 'CONSOLIDADA'].includes(normalized)) {
    return 'aprovado';
  }

  if (['PENDENTE', 'SUGERIDA'].includes(normalized)) {
    return 'pendente';
  }

  if (['REPROVADO', 'REJEITADO'].includes(normalized)) {
    return 'rejeitado';
  }

  if (normalized === 'ATIVO') {
    return 'ativo';
  }

  if (normalized === 'INATIVO') {
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
  const label =
    kind === 'origemMatch'
      ? getOrigemMatchLabel(value as never)
      : getHomologacaoLabel(value);

  return (
    <Chip
      size="small"
      label={label}
      sx={{
        color: colorSet.color,
        backgroundColor: colorSet.bg,
        border: 'none',
      }}
    />
  );
}
