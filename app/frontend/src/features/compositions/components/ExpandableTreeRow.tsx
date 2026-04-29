import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowRightIcon from '@mui/icons-material/KeyboardArrowRight';
import {
  Box,
  CircularProgress,
  Collapse,
  IconButton,
  TableCell,
  TableRow,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { servicesApi } from '../../../shared/services/api/servicesApi';
import type { ComposicaoComponenteResponse } from '../../../shared/types/contracts/servicos';
import { formatCurrency } from '../../../shared/utils/format';

interface Props {
  item: {
    id: string;
    descricao: string;
    codigo_origem?: string | null;
    unidade_medida?: string;
    custo_unitario?: number | string;
    tipo_recurso?: string | null;
  };
  depth?: number;
  maxDepth?: number;
  isExpandable?: boolean;
  isSelected?: boolean;
  onSelect?: (id: string) => void;
}

export function ExpandableTreeRow({ item, depth = 0, maxDepth = 5, isExpandable, isSelected, onSelect }: Props) {
  const [open, setOpen] = useState(false);
  const canExpand = depth < maxDepth && (isExpandable ?? item.tipo_recurso === 'SERVICO');

  const componentesQuery = useQuery({
    queryKey: ['composicao-componentes', item.id],
    queryFn: () => servicesApi.getComponentes(item.id),
    enabled: open && canExpand,
    staleTime: 5 * 60 * 1000,
  });

  const indent = depth * 24;

  const handleRowClick = () => {
    onSelect?.(item.id);
  };

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    setOpen(!open);
  };

  return (
    <>
      <TableRow
        hover
        selected={isSelected}
        onClick={handleRowClick}
        sx={{ cursor: onSelect ? 'pointer' : 'default', '& > *': { borderBottom: 'unset' } }}
      >
        <TableCell sx={{ py: 1, px: 1.5 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', pl: `${indent}px` }}>
            {canExpand ? (
              <IconButton
                size="small"
                onClick={handleToggle}
                sx={{ mr: 0.5 }}
                data-testid={`expand-toggle-${item.id}`}
                aria-label={open ? `Recolher ${item.descricao}` : `Expandir ${item.descricao}`}
              >
                {open ? <KeyboardArrowDownIcon fontSize="small" /> : <KeyboardArrowRightIcon fontSize="small" />}
              </IconButton>
            ) : (
              <Box sx={{ width: 28, mr: 0.5 }} />
            )}
            <Typography variant="body2" fontWeight={canExpand ? 600 : 400}>
              {item.descricao}
            </Typography>
          </Box>
        </TableCell>
        <TableCell sx={{ py: 1, px: 1.5 }}>
          <Typography variant="body2" color="text.secondary">
            {item.codigo_origem ?? '—'}
          </Typography>
        </TableCell>
        <TableCell sx={{ py: 1, px: 1.5 }}>
          <Typography variant="body2" color="text.secondary">
            {item.unidade_medida ?? '—'}
          </Typography>
        </TableCell>
        <TableCell sx={{ py: 1, px: 1.5, textAlign: 'right' }}>
          <Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>
            {formatCurrency(Number(item.custo_unitario ?? 0))}
          </Typography>
        </TableCell>
        <TableCell sx={{ py: 1, px: 1.5 }}>
          <Typography variant="caption" color="text.secondary">
            {item.tipo_recurso ?? '—'}
          </Typography>
        </TableCell>
      </TableRow>

      {canExpand && (
        <TableRow>
          <TableCell colSpan={5} sx={{ py: 0, px: 0, border: 0 }}>
            <Collapse in={open} timeout="auto" unmountOnExit>
              <Box sx={{ py: 0.5 }}>
                {componentesQuery.isLoading ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, pl: `${indent + 28}px`, py: 1 }}>
                    <CircularProgress size={16} />
                    <Typography variant="caption" color="text.secondary">
                      Carregando componentes...
                    </Typography>
                  </Box>
                ) : componentesQuery.isError ? (
                  <Box sx={{ pl: `${indent + 28}px`, py: 1 }}>
                    <Typography variant="caption" color="error">
                      Erro ao carregar componentes.
                    </Typography>
                  </Box>
                ) : componentesQuery.data?.length ? (
                  componentesQuery.data.map((child: ComposicaoComponenteResponse) => (
                    <ExpandableTreeRow
                      key={child.id}
                      item={{
                        id: child.insumo_filho_id,
                        descricao: child.descricao_filho,
                        codigo_origem: child.codigo_origem ?? null,
                        unidade_medida: child.unidade_medida,
                        custo_unitario: child.custo_unitario,
                        tipo_recurso: child.tipo_recurso,
                      }}
                      depth={depth + 1}
                      maxDepth={maxDepth}
                      isExpandable={child.tipo_recurso === 'SERVICO'}
                    />
                  ))
                ) : (
                  <Box sx={{ pl: `${indent + 28}px`, py: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      Sem componentes.
                    </Typography>
                  </Box>
                )}
              </Box>
            </Collapse>
          </TableCell>
        </TableRow>
      )}
    </>
  );
}
