import { useState } from 'react';
import {
  Box,
  Button,
  Chip,
  Collapse,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import { useQuery } from '@tanstack/react-query';
import { formatCurrency } from '../../../shared/utils/format';
import type { CpuItemDetalhado } from '../../../shared/services/api/proposalsApi';
import { proposalsApi } from '../../../shared/services/api/proposalsApi';
import { AlocacaoRecursoDialog } from './AlocacaoRecursoDialog';

interface ComposicaoRowsProps {
  propostaId: string;
  itemId: string;
}

function ComposicaoRows({ propostaId, itemId }: ComposicaoRowsProps) {
  const { data: composicoes = [], isLoading } = useQuery({
    queryKey: ['composicoes', propostaId, itemId],
    queryFn: () => proposalsApi.getComposicoes(propostaId, itemId),
  });

  const [allocDialog, setAllocDialog] = useState<{ composicaoId: string; descricao: string } | null>(null);

  if (isLoading) {
    return (
      <TableRow>
        <TableCell colSpan={6}>
          <Typography variant="caption">Carregando insumos...</Typography>
        </TableCell>
      </TableRow>
    );
  }

  return (
    <>
      {composicoes.map((c) => (
        <TableRow key={c.id} sx={{ bgcolor: 'action.hover' }}>
          <TableCell sx={{ pl: 6 }}>
            <Chip
              label={c.tipo_recurso ?? 'MAT'}
              size="small"
              color={
                c.tipo_recurso === 'MO' ? 'info'
                : c.tipo_recurso === 'EQUIPAMENTO' ? 'warning'
                : 'default'
              }
              sx={{ mr: 1 }}
            />
            {c.descricao_insumo}
          </TableCell>
          <TableCell>{c.unidade_medida}</TableCell>
          <TableCell>{parseFloat(c.quantidade_consumo).toFixed(4)}</TableCell>
          <TableCell>{c.custo_unitario_insumo ? formatCurrency(parseFloat(c.custo_unitario_insumo)) : '—'}</TableCell>
          <TableCell>{c.custo_total_insumo ? formatCurrency(parseFloat(c.custo_total_insumo)) : '—'}</TableCell>
          <TableCell>
            <Button
              size="small"
              variant="text"
              startIcon={<AddCircleOutlineIcon fontSize="small" />}
              onClick={() => setAllocDialog({ composicaoId: c.id, descricao: c.descricao_insumo })}
            >
              Alocar
            </Button>
          </TableCell>
        </TableRow>
      ))}
      {composicoes.length === 0 && (
        <TableRow sx={{ bgcolor: 'action.hover' }}>
          <TableCell colSpan={6} sx={{ pl: 6 }}>
            <Typography variant="caption" color="text.secondary">
              Sem insumos registrados para este item.
            </Typography>
          </TableCell>
        </TableRow>
      )}
      {allocDialog && (
        <AlocacaoRecursoDialog
          open={!!allocDialog}
          onClose={() => setAllocDialog(null)}
          propostaId={propostaId}
          composicaoId={allocDialog.composicaoId}
          composicaoDescricao={allocDialog.descricao}
        />
      )}
    </>
  );
}

interface CpuItemRowProps {
  item: CpuItemDetalhado;
  propostaId: string;
}

function CpuItemRow({ item, propostaId }: CpuItemRowProps) {
  const [open, setOpen] = useState(false);
  const bdi = item.percentual_indireto
    ? `${(parseFloat(item.percentual_indireto) * 100).toFixed(1)}%`
    : '0%';

  return (
    <>
      <TableRow hover>
        <TableCell sx={{ width: 40 }}>
          <IconButton size="small" onClick={() => setOpen(!open)}>
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell>
          <Typography variant="caption" color="text.secondary">{item.codigo}</Typography>
        </TableCell>
        <TableCell>
          <Tooltip title={item.descricao}>
            <Typography variant="body2" noWrap sx={{ maxWidth: 280 }}>{item.descricao}</Typography>
          </Tooltip>
        </TableCell>
        <TableCell>{item.unidade_medida}</TableCell>
        <TableCell align="right">{parseFloat(item.quantidade).toFixed(2)}</TableCell>
        <TableCell align="right">{item.custo_material_unitario ? formatCurrency(parseFloat(item.custo_material_unitario)) : '—'}</TableCell>
        <TableCell align="right">{item.custo_mao_obra_unitario ? formatCurrency(parseFloat(item.custo_mao_obra_unitario)) : '—'}</TableCell>
        <TableCell align="right">{item.custo_equipamento_unitario ? formatCurrency(parseFloat(item.custo_equipamento_unitario)) : '—'}</TableCell>
        <TableCell align="right">{item.custo_direto_unitario ? formatCurrency(parseFloat(item.custo_direto_unitario)) : '—'}</TableCell>
        <TableCell align="right">
          <Chip label={bdi} size="small" variant="outlined" />
        </TableCell>
        <TableCell align="right" sx={{ fontWeight: 'bold' }}>
          {item.preco_total ? formatCurrency(parseFloat(item.preco_total)) : '—'}
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell colSpan={11} sx={{ py: 0, border: 0 }}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ m: 1 }}>
              <Typography variant="caption" color="text.secondary" sx={{ ml: 5 }}>
                Insumos
              </Typography>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ bgcolor: 'action.hover' }}>
                    <TableCell sx={{ pl: 6 }}>Insumo</TableCell>
                    <TableCell>Und</TableCell>
                    <TableCell>Qtd</TableCell>
                    <TableCell>Custo Unit.</TableCell>
                    <TableCell>Custo Total</TableCell>
                    <TableCell>Ações</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <ComposicaoRows propostaId={propostaId} itemId={item.id} />
                </TableBody>
              </Table>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
}

interface CpuTableProps {
  itens: CpuItemDetalhado[];
  propostaId: string;
}

export function CpuTable({ itens, propostaId }: CpuTableProps) {
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell />
          <TableCell>Código</TableCell>
          <TableCell>Descrição</TableCell>
          <TableCell>Und</TableCell>
          <TableCell align="right">Qtd</TableCell>
          <TableCell align="right">Mat. Unit.</TableCell>
          <TableCell align="right">MO Unit.</TableCell>
          <TableCell align="right">Equip. Unit.</TableCell>
          <TableCell align="right">Dir. Unit.</TableCell>
          <TableCell align="right">BDI</TableCell>
          <TableCell align="right">Total</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {itens.map((item) => (
          <CpuItemRow key={item.id} item={item} propostaId={propostaId} />
        ))}
        {itens.length === 0 && (
          <TableRow>
            <TableCell colSpan={11} align="center" sx={{ py: 4 }}>
              <Typography color="text.secondary">
                Nenhum item de CPU gerado ainda.
              </Typography>
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}
