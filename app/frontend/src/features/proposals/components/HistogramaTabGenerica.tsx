import { useState } from 'react';
import {
  Chip,
  IconButton,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { DivergenciaOut } from '../../../shared/types/contracts/proposta_pc';
import { histogramaApi } from '../../../shared/services/api/histogramaApi';

interface GenericItem {
  id: string;
  descricao?: string | null;
  equipamento?: string | null;
  epi?: string | null;
  discriminacao_encargo?: string | null;
  codigo_origem?: string | null;
  valor_bcu_snapshot?: number | null;
  editado_manualmente: boolean;
  [key: string]: any;
}

interface Props {
  propostaId: string;
  tabela: 'equipamento' | 'epi' | 'ferramenta' | 'encargo' | 'mobilizacao';
  items: GenericItem[];
  divergencias: DivergenciaOut[];
  columns: { key: string; label: string; editable?: boolean; numeric?: boolean }[];
}

function fmt(value: number | null | undefined, decimals = 2): string {
  if (value == null) return '—';
  return new Intl.NumberFormat('pt-BR', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(value);
}

const headCell = { fontWeight: 700, fontSize: '0.72rem', textTransform: 'uppercase' as const, color: 'text.secondary', whiteSpace: 'nowrap' as const, py: 1, px: 1.5 };
const dataCell = { fontSize: '0.8rem', py: 0.75, px: 1.5 };
const numCell = { ...dataCell, textAlign: 'right' as const, fontVariantNumeric: 'tabular-nums' };

function getDescricao(item: GenericItem): string {
  return item.descricao || item.equipamento || item.epi || item.discriminacao_encargo || '—';
}

export function HistogramaTabGenerica({ propostaId, tabela, items, divergencias, columns }: Props) {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<Record<string, Record<string, any>>>({});

  const editarMutation = useMutation({
    mutationFn: ({ itemId, payload }: { itemId: string; payload: Record<string, any> }) =>
      histogramaApi.editarItem(propostaId, tabela, itemId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['histograma', propostaId] });
    },
  });

  const aceitarMutation = useMutation({
    mutationFn: (itemId: string) => histogramaApi.aceitarBcu(propostaId, tabela, itemId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['histograma', propostaId] });
    },
  });

  const divergeMap = new Map<string, DivergenciaOut[]>();
  for (const d of divergencias) {
    const tabelaMap: Record<string, string> = { equipamento: 'equipamento', epi: 'epi', ferramenta: 'ferramenta' };
    if (tabelaMap[tabela] === d.tabela) {
      const arr = divergeMap.get(d.item_id) || [];
      arr.push(d);
      divergeMap.set(d.item_id, arr);
    }
  }

  const handleChange = (itemId: string, field: string, value: string) => {
    setEditing((prev) => ({
      ...prev,
      [itemId]: { ...prev[itemId], [field]: value === '' ? null : parseFloat(value.replace(',', '.')) },
    }));
  };

  const handleBlur = (item: GenericItem) => {
    const payload = editing[item.id];
    if (!payload || Object.keys(payload).length === 0) return;
    editarMutation.mutate({ itemId: item.id, payload });
    setEditing((prev) => { const n = { ...prev }; delete n[item.id]; return n; });
  };

  return (
    <TableContainer component={Paper} variant="outlined">
      <Table size="small" stickyHeader>
        <TableHead>
          <TableRow>
            <TableCell sx={headCell}>Descrição</TableCell>
            {columns.map((col) => (
              <TableCell key={col.key} sx={{ ...headCell, textAlign: col.numeric ? 'right' : 'left' }}>{col.label}</TableCell>
            ))}
            <TableCell sx={{ ...headCell, textAlign: 'right' }}>Snapshot BCU</TableCell>
            <TableCell sx={headCell} align="center">Status</TableCell>
            <TableCell sx={headCell} align="right">Ações</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {items.map((item) => {
            const divergeList = divergeMap.get(item.id);
            const isEditing = editing[item.id] || {};
            return (
              <TableRow key={item.id} hover sx={{ bgcolor: divergeList ? 'warning.50' : undefined }}>
                <TableCell sx={dataCell}>
                  <Typography variant="body2" fontWeight={500}>{getDescricao(item)}</Typography>
                  {item.codigo_origem && (
                    <Typography variant="caption" color="text.secondary">{item.codigo_origem}</Typography>
                  )}
                </TableCell>
                {columns.map((col) => (
                  <TableCell key={col.key} sx={col.numeric ? numCell : dataCell}>
                    {col.editable ? (
                      <TextField
                        size="small"
                        variant="standard"
                        type="number"
                        value={isEditing[col.key] !== undefined ? (isEditing[col.key] ?? '') : (item[col.key] ?? '')}
                        onChange={(e) => handleChange(item.id, col.key, e.target.value)}
                        onBlur={() => handleBlur(item)}
                        inputProps={{ style: { textAlign: col.numeric ? 'right' : 'left', fontSize: '0.85rem' } }}
                      />
                    ) : (
                      fmt(item[col.key], col.numeric ? 2 : 0)
                    )}
                  </TableCell>
                ))}
                <TableCell sx={numCell}>{fmt(item.valor_bcu_snapshot ?? null)}</TableCell>
                <TableCell sx={dataCell} align="center">
                  <Stack direction="row" spacing={0.5} justifyContent="center">
                    {item.editado_manualmente && <Chip label="Editado" size="small" color="info" variant="outlined" />}
                    {divergeList && (
                      <Tooltip title={`Divergência: snapshot ${fmt(divergeList[0].valor_snapshot)} vs BCU ${fmt(divergeList[0].valor_atual_bcu)}`}>
                        <Chip label="Diverge" size="small" color="warning" icon={<WarningAmberIcon fontSize="small" />} />
                      </Tooltip>
                    )}
                  </Stack>
                </TableCell>
                <TableCell sx={dataCell} align="right">
                  {divergeList && (
                    <Tooltip title="Aceitar valor BCU atual">
                      <IconButton size="small" color="success" onClick={() => aceitarMutation.mutate(item.id)}>
                        <CheckCircleOutlineIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
