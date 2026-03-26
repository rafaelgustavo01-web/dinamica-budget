import { Chip } from '@mui/material';

import {
  getHomologacaoLabel,
  getOrigemMatchLabel,
} from '../utils/format';

interface StatusBadgeProps {
  value: string;
  kind?: 'status' | 'origemMatch';
}

export function StatusBadge({
  value,
  kind = 'status',
}: StatusBadgeProps) {
  const label =
    kind === 'origemMatch'
      ? getOrigemMatchLabel(value as never)
      : getHomologacaoLabel(value);

  let color: 'default' | 'success' | 'warning' | 'error' | 'secondary' = 'default';

  if (['APROVADO', 'VALIDADA', 'CONSOLIDADA'].includes(value)) {
    color = 'success';
  } else if (['PENDENTE', 'SUGERIDA'].includes(value)) {
    color = 'warning';
  } else if (['REPROVADO'].includes(value)) {
    color = 'error';
  } else if (['ASSOCIACAO_DIRETA', 'PROPRIA_CLIENTE'].includes(value)) {
    color = 'secondary';
  }

  return <Chip size="small" color={color} label={label} />;
}
