import AddIcon from '@mui/icons-material/Add';
import ConstructionOutlinedIcon from '@mui/icons-material/ConstructionOutlined';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import EngineeringOutlinedIcon from '@mui/icons-material/EngineeringOutlined';
import HardwareOutlinedIcon from '@mui/icons-material/HardwareOutlined';
import LocalShippingOutlinedIcon from '@mui/icons-material/LocalShippingOutlined';
import SafetyDividerOutlinedIcon from '@mui/icons-material/SafetyDividerOutlined';
import SecurityOutlinedIcon from '@mui/icons-material/SecurityOutlined';
import WorkOutlineOutlinedIcon from '@mui/icons-material/WorkOutlineOutlined';
import {
  Alert,
  Box,
  Button,
  Chip,
  Paper,
  Skeleton,
  Stack,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tooltip,
  Typography,
} from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { ConfirmationDialog } from '../../shared/components/ConfirmationDialog';
import { HelpTooltip } from '../../shared/components/HelpTooltip';
import { PageHeader } from '../../shared/components/PageHeader';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import type {
  BcuEncargoItem,
  BcuEquipamentoItem,
  BcuEpiItem,
  BcuFerramentaItem,
  BcuMaoObraItem,
  BcuMobilizacaoItem,
} from '../../shared/services/api/bcuApi';
import { bcuApi } from '../../shared/services/api/bcuApi';
import { bcuItemApi } from '../../shared/services/api/bcuItemApi';
import { BcuItemDialog, type BcuItemType } from './BcuItemDialog';

// ── Helpers ──────────────────────────────────────────────────────────────────

function fmt(value: number | null | undefined, decimals = 2): string {
  if (value == null) return '—';
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

function fmtPct(value: number | null | undefined): string {
  if (value == null) return '—';
  return new Intl.NumberFormat('pt-BR', {
    style: 'percent',
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(value);
}

const headCell = {
  fontWeight: 700,
  fontSize: '0.72rem',
  textTransform: 'uppercase' as const,
  color: 'text.secondary',
  whiteSpace: 'nowrap' as const,
  py: 1,
  px: 1.5,
};

const dataCell = {
  fontSize: '0.8rem',
  py: 0.75,
  px: 1.5,
};

const numCell = {
  ...dataCell,
  textAlign: 'right' as const,
  fontVariantNumeric: 'tabular-nums',
};

// ── Tab Panels ───────────────────────────────────────────────────────────────

function MaoObraTab({ cabecalhoId, onEdit, onDelete }: { cabecalhoId: string; onEdit: (item: BcuMaoObraItem) => void; onDelete: (id: string) => void }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['bcu-mao-obra', cabecalhoId],
    queryFn: () => bcuApi.getMaoObra(cabecalhoId),
  });

  if (isLoading) return <TableSkeleton rows={12} cols={8} />;
  if (error || !data) return <Alert severity="error">Erro ao carregar mão de obra.</Alert>;

  return (
    <Box sx={{ overflowX: 'auto', width: '100%' }}>
      <Stack direction="row" spacing={1} sx={{ p: 1.5 }} justifyContent="flex-end">
        <Button size="small" startIcon={<AddIcon />} onClick={() => onEdit({ id: '', descricao_funcao: '' } as BcuMaoObraItem)}>
          Novo
        </Button>
      </Stack>
      <Table size="small" stickyHeader sx={{ minWidth: 1200 }}>
        <TableHead>
          <TableRow>
            <TableCell sx={{ ...headCell, position: 'sticky', left: 0, zIndex: 3, bgcolor: 'background.paper', minWidth: 180 }}>Função</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right', minWidth: 55 }}>Qtd</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right', minWidth: 95 }}>Salário</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right', minWidth: 95 }}>Reajuste</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right', minWidth: 90 }}>Encargos %</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right', minWidth: 90 }}>Refeição</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right', minWidth: 90 }}>Vale Alim.</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right', minWidth: 100 }}>Plano Saúde</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right', minWidth: 80 }}>EPI (R$)</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right', minWidth: 80 }}>Uniforme</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right', minWidth: 90 }}>Seguro Vida</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right', minWidth: 95 }}>Custo/H (R$)</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right', minWidth: 105 }}>Custo Mensal</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right', minWidth: 105 }}>Mobilização</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right', minWidth: 100 }}>Ações</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data.length === 0 && (
            <TableRow>
              <TableCell colSpan={15} sx={{ ...dataCell, textAlign: 'center', py: 4, color: 'text.secondary' }}>
                Nenhuma função cadastrada.
              </TableCell>
            </TableRow>
          )}
          {data.map((item: BcuMaoObraItem) => (
            <TableRow key={item.id} hover>
              <TableCell sx={{ ...dataCell, position: 'sticky', left: 0, zIndex: 1, bgcolor: 'background.paper' }}>
                <Typography variant="body2" fontWeight={500}>{item.descricao_funcao}</Typography>
              </TableCell>
              <TableCell sx={numCell}>{fmt(item.quantidade, 0)}</TableCell>
              <TableCell sx={numCell}>R$ {fmt(item.salario)}</TableCell>
              <TableCell sx={numCell}>R$ {fmt(item.previsao_reajuste)}</TableCell>
              <TableCell sx={numCell}>{fmtPct(item.encargos_percent ? item.encargos_percent / 100 : null)}</TableCell>
              <TableCell sx={numCell}>R$ {fmt(item.refeicao)}</TableCell>
              <TableCell sx={numCell}>R$ {fmt(item.vale_alimentacao)}</TableCell>
              <TableCell sx={numCell}>R$ {fmt(item.plano_saude)}</TableCell>
              <TableCell sx={numCell}>R$ {fmt(item.epi_val)}</TableCell>
              <TableCell sx={numCell}>R$ {fmt(item.uniforme_val)}</TableCell>
              <TableCell sx={numCell}>R$ {fmt(item.seguro_vida)}</TableCell>
              <TableCell sx={numCell}>R$ {fmt(item.custo_unitario_h)}</TableCell>
              <TableCell sx={{ ...numCell, fontWeight: 600, color: 'primary.main' }}>R$ {fmt(item.custo_mensal)}</TableCell>
              <TableCell sx={numCell}>R$ {fmt(item.mobilizacao)}</TableCell>
              <TableCell sx={dataCell}>
                <Stack direction="row" spacing={0.5}>
                  <Button size="small" startIcon={<EditOutlinedIcon />} onClick={() => onEdit(item)}>Editar</Button>
                  <Button size="small" color="error" startIcon={<DeleteOutlineIcon />} onClick={() => onDelete(item.id)}>Excluir</Button>
                </Stack>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Box>
  );
}

function EquipamentosTab({ cabecalhoId, onEdit, onDelete }: { cabecalhoId: string; onEdit: (item: BcuEquipamentoItem) => void; onDelete: (id: string) => void }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['bcu-equipamentos', cabecalhoId],
    queryFn: () => bcuApi.getEquipamentos(cabecalhoId),
  });

  if (isLoading) return <TableSkeleton rows={20} cols={7} />;
  if (error || !data) return <Alert severity="error">Erro ao carregar equipamentos.</Alert>;

  return (
    <Stack spacing={2}>
      {data.premissa && (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle2" fontWeight={700} mb={1}>Premissas</Typography>
          <Stack direction="row" spacing={3}>
            <Box>
              <Typography variant="caption" color="text.secondary">Horas/mês</Typography>
              <Typography variant="body2" fontWeight={600}>{fmt(data.premissa.horas_mes, 0)} h</Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Gasolina</Typography>
              <Typography variant="body2" fontWeight={600}>R$ {fmt(data.premissa.preco_gasolina_l)}/L</Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Diesel</Typography>
              <Typography variant="body2" fontWeight={600}>R$ {fmt(data.premissa.preco_diesel_l)}/L</Typography>
            </Box>
          </Stack>
        </Paper>
      )}
      <Stack direction="row" spacing={1} sx={{ px: 1.5 }} justifyContent="flex-end">
        <Button size="small" startIcon={<AddIcon />} onClick={() => onEdit({ id: '', equipamento: '' } as BcuEquipamentoItem)}>
          Novo
        </Button>
      </Stack>
      <TableContainer>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={headCell}>Cód</TableCell>
              <TableCell sx={headCell}>Equipamento</TableCell>
              <TableCell sx={headCell}>Comb.</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Consumo (l/h)</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Aluguel (R$/h)</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Combust. (R$/h)</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>MO (R$/h)</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>H Produt.</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>H Improd.</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Total/Mês</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Aluguel Mens.</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Ações</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.items.length === 0 && (
              <TableRow>
                <TableCell colSpan={12} sx={{ ...dataCell, textAlign: 'center', py: 4, color: 'text.secondary' }}>
                  Nenhum equipamento cadastrado.
                </TableCell>
              </TableRow>
            )}
            {data.items.map((item: BcuEquipamentoItem) => (
              <TableRow key={item.id} hover>
                <TableCell sx={dataCell}>{item.codigo ?? '—'}</TableCell>
                <TableCell sx={dataCell}>
                  <Tooltip title={item.equipamento} placement="top">
                    <Typography variant="body2" fontWeight={500} sx={{ maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {item.equipamento}
                    </Typography>
                  </Tooltip>
                </TableCell>
                <TableCell sx={dataCell}>
                  <Chip label={item.combustivel_utilizado ?? '—'} size="small" variant="outlined"
                    color={item.combustivel_utilizado === 'D' ? 'warning' : item.combustivel_utilizado === 'G' ? 'info' : 'default'} />
                </TableCell>
                <TableCell sx={numCell}>{fmt(item.consumo_l_h, 1)}</TableCell>
                <TableCell sx={numCell}>R$ {fmt(item.aluguel_r_h)}</TableCell>
                <TableCell sx={numCell}>R$ {fmt(item.combustivel_r_h)}</TableCell>
                <TableCell sx={numCell}>R$ {fmt(item.mao_obra_r_h)}</TableCell>
                <TableCell sx={numCell}>R$ {fmt(item.hora_produtiva)}</TableCell>
                <TableCell sx={numCell}>R$ {fmt(item.hora_improdutiva)}</TableCell>
                <TableCell sx={{ ...numCell, fontWeight: 600, color: 'primary.main' }}>R$ {fmt(item.mes)}</TableCell>
                <TableCell sx={numCell}>R$ {fmt(item.aluguel_mensal)}</TableCell>
                <TableCell sx={dataCell}>
                  <Stack direction="row" spacing={0.5}>
                    <Button size="small" startIcon={<EditOutlinedIcon />} onClick={() => onEdit(item)}>Editar</Button>
                    <Button size="small" color="error" startIcon={<DeleteOutlineIcon />} onClick={() => onDelete(item.id)}>Excluir</Button>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Stack>
  );
}

function EncargosTab({ cabecalhoId, onEdit, onDelete }: { cabecalhoId: string; onEdit: (item: BcuEncargoItem) => void; onDelete: (id: string) => void }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['bcu-encargos', cabecalhoId],
    queryFn: () => bcuApi.getEncargos(cabecalhoId),
  });

  if (isLoading) return <TableSkeleton rows={20} cols={5} />;
  if (error || !data) return <Alert severity="error">Erro ao carregar encargos.</Alert>;

  return (
    <Box>
      <Stack direction="row" spacing={1} sx={{ p: 1.5 }} justifyContent="flex-end">
        <Button size="small" startIcon={<AddIcon />} onClick={() => onEdit({ id: '', tipo_encargo: 'HORISTA', discriminacao_encargo: '' } as BcuEncargoItem)}>
          Novo
        </Button>
      </Stack>
      <TableContainer>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={headCell}>Tipo</TableCell>
              <TableCell sx={headCell}>Grupo</TableCell>
              <TableCell sx={headCell}>Código</TableCell>
              <TableCell sx={headCell}>Discriminação</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Taxa %</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Ações</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} sx={{ ...dataCell, textAlign: 'center', py: 4, color: 'text.secondary' }}>
                  Nenhum encargo cadastrado.
                </TableCell>
              </TableRow>
            )}
            {data.map((item: BcuEncargoItem) => (
              <TableRow key={item.id} hover>
                <TableCell sx={dataCell}>
                  {item.tipo_encargo && (
                    <Chip
                      label={item.tipo_encargo}
                      size="small"
                      color={item.tipo_encargo === 'HORISTA' ? 'info' : 'secondary'}
                      variant="outlined"
                    />
                  )}
                </TableCell>
                <TableCell sx={dataCell}>
                  {item.grupo && <Chip label={item.grupo} size="small" color="primary" variant="outlined" />}
                </TableCell>
                <TableCell sx={dataCell}>{item.codigo_grupo ?? '—'}</TableCell>
                <TableCell sx={dataCell}>{item.discriminacao_encargo}</TableCell>
                <TableCell sx={numCell}>{fmtPct(item.taxa_percent != null ? item.taxa_percent / 100 : null)}</TableCell>
                <TableCell sx={dataCell}>
                  <Stack direction="row" spacing={0.5}>
                    <Button size="small" startIcon={<EditOutlinedIcon />} onClick={() => onEdit(item)}>Editar</Button>
                    <Button size="small" color="error" startIcon={<DeleteOutlineIcon />} onClick={() => onDelete(item.id)}>Excluir</Button>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

function EpiTab({ cabecalhoId, onEdit, onDelete }: { cabecalhoId: string; onEdit: (item: BcuEpiItem) => void; onDelete: (id: string) => void }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['bcu-epi', cabecalhoId],
    queryFn: () => bcuApi.getEpi(cabecalhoId),
  });

  if (isLoading) return <TableSkeleton rows={15} cols={6} />;
  if (error || !data) return <Alert severity="error">Erro ao carregar EPI.</Alert>;

  return (
    <Box>
      <Stack direction="row" spacing={1} sx={{ p: 1.5 }} justifyContent="flex-end">
        <Button size="small" startIcon={<AddIcon />} onClick={() => onEdit({ id: '', epi: '' } as BcuEpiItem)}>
          Novo
        </Button>
      </Stack>
      <TableContainer>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={headCell}>EPI / Uniforme</TableCell>
              <TableCell sx={headCell}>Unid.</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Custo Unit.</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Qtd</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Vida Útil (meses)</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Custo/Mês</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Ações</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} sx={{ ...dataCell, textAlign: 'center', py: 4, color: 'text.secondary' }}>
                  Nenhum EPI cadastrado.
                </TableCell>
              </TableRow>
            )}
            {data.map((item: BcuEpiItem) => (
              <TableRow key={item.id} hover>
                <TableCell sx={dataCell}>
                  <Typography variant="body2" fontWeight={500}>{item.epi}</Typography>
                </TableCell>
                <TableCell sx={dataCell}>{item.unidade ?? '—'}</TableCell>
                <TableCell sx={numCell}>R$ {fmt(item.custo_unitario)}</TableCell>
                <TableCell sx={numCell}>{fmt(item.quantidade, 1)}</TableCell>
                <TableCell sx={numCell}>{fmt(item.vida_util_meses, 0)} meses</TableCell>
                <TableCell sx={{ ...numCell, fontWeight: 600, color: 'primary.main' }}>R$ {fmt(item.custo_epi_mes)}</TableCell>
                <TableCell sx={dataCell}>
                  <Stack direction="row" spacing={0.5}>
                    <Button size="small" startIcon={<EditOutlinedIcon />} onClick={() => onEdit(item)}>Editar</Button>
                    <Button size="small" color="error" startIcon={<DeleteOutlineIcon />} onClick={() => onDelete(item.id)}>Excluir</Button>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

function FerramentasTab({ cabecalhoId, onEdit, onDelete }: { cabecalhoId: string; onEdit: (item: BcuFerramentaItem) => void; onDelete: (id: string) => void }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['bcu-ferramentas', cabecalhoId],
    queryFn: () => bcuApi.getFerramentas(cabecalhoId),
  });

  if (isLoading) return <TableSkeleton rows={20} cols={5} />;
  if (error || !data) return <Alert severity="error">Erro ao carregar ferramentas.</Alert>;

  const total = data.reduce((s: number, i: BcuFerramentaItem) => s + (i.preco_total ?? 0), 0);

  return (
    <Stack spacing={2}>
      <Stack direction="row" spacing={1} sx={{ px: 1.5 }} justifyContent="flex-end">
        <Button size="small" startIcon={<AddIcon />} onClick={() => onEdit({ id: '', descricao: '' } as BcuFerramentaItem)}>
          Novo
        </Button>
      </Stack>
      <TableContainer>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={headCell}>Item</TableCell>
              <TableCell sx={headCell}>Unidade</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Qtd</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Preço Unit. (R$)</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Total (R$)</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Ações</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} sx={{ ...dataCell, textAlign: 'center', py: 4, color: 'text.secondary' }}>
                  Nenhuma ferramenta cadastrada.
                </TableCell>
              </TableRow>
            )}
            {data.map((item: BcuFerramentaItem) => (
              <TableRow key={item.id} hover>
                <TableCell sx={dataCell}>{item.item ?? item.descricao ?? '—'}</TableCell>
                <TableCell sx={dataCell}>{item.unidade ?? '—'}</TableCell>
                <TableCell sx={{ ...numCell }}>{item.quantidade != null ? fmt(item.quantidade) : '—'}</TableCell>
                <TableCell sx={{ ...numCell }}>R$ {fmt(item.preco)}</TableCell>
                <TableCell sx={{ ...numCell, fontWeight: 600 }}>R$ {fmt(item.preco_total)}</TableCell>
                <TableCell sx={dataCell}>
                  <Stack direction="row" spacing={0.5}>
                    <Button size="small" startIcon={<EditOutlinedIcon />} onClick={() => onEdit(item)}>Editar</Button>
                    <Button size="small" color="error" startIcon={<DeleteOutlineIcon />} onClick={() => onDelete(item.id)}>Excluir</Button>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
            <TableRow>
              <TableCell colSpan={4} sx={{ ...dataCell, fontWeight: 700, textAlign: 'right' }}>TOTAL</TableCell>
              <TableCell sx={{ ...numCell, fontWeight: 700, color: 'primary.main' }}>R$ {fmt(total)}</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    </Stack>
  );
}

function MobilizacaoTab({ cabecalhoId, onEdit, onDelete }: { cabecalhoId: string; onEdit: (item: BcuMobilizacaoItem) => void; onDelete: (id: string) => void }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['bcu-mobilizacao', cabecalhoId],
    queryFn: () => bcuApi.getMobilizacao(cabecalhoId),
  });

  if (isLoading) return <TableSkeleton rows={10} cols={6} />;
  if (error || !data) return <Alert severity="error">Erro ao carregar mobilização.</Alert>;

  // Get all unique function columns
  const funcaoCols = Array.from(
    new Set(data.flatMap((i: BcuMobilizacaoItem) => i.quantidades_funcao.map((q) => q.coluna_funcao)))
  );

  return (
    <Box>
      <Stack direction="row" spacing={1} sx={{ p: 1.5 }} justifyContent="flex-end">
        <Button size="small" startIcon={<AddIcon />} onClick={() => onEdit({ id: '', descricao: '', quantidades_funcao: [] } as unknown as BcuMobilizacaoItem)}>
          Novo
        </Button>
      </Stack>
      <TableContainer>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={headCell}>Exame / Evento</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Valor Unit.</TableCell>
              {funcaoCols.map((col) => (
                <TableCell key={col} sx={{ ...headCell, textAlign: 'right' }}>{col}</TableCell>
              ))}
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Ações</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.length === 0 && (
              <TableRow>
                <TableCell colSpan={funcaoCols.length + 3} sx={{ ...dataCell, textAlign: 'center', py: 4, color: 'text.secondary' }}>
                  Nenhum item de mobilização cadastrado.
                </TableCell>
              </TableRow>
            )}
            {data.map((item: BcuMobilizacaoItem) => {
              const qMap = new Map(item.quantidades_funcao.map((q) => [q.coluna_funcao, q.quantidade]));
              return (
                <TableRow key={item.id} hover>
                  <TableCell sx={dataCell}>{item.descricao}</TableCell>
                  <TableCell sx={numCell}>{fmt(item.funcao ? parseFloat(item.funcao) : null)}</TableCell>
                  {funcaoCols.map((col) => (
                    <TableCell key={col} sx={numCell}>R$ {fmt(qMap.get(col) ?? null)}</TableCell>
                  ))}
                  <TableCell sx={dataCell}>
                    <Stack direction="row" spacing={0.5}>
                      <Button size="small" startIcon={<EditOutlinedIcon />} onClick={() => onEdit(item)}>Editar</Button>
                      <Button size="small" color="error" startIcon={<DeleteOutlineIcon />} onClick={() => onDelete(item.id)}>Excluir</Button>
                    </Stack>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

function TableSkeleton({ rows, cols }: { rows: number; cols: number }) {
  return (
    <Stack spacing={1} p={1}>
      {Array.from({ length: rows }).map((_, i) => (
        <Stack key={i} direction="row" spacing={1}>
          {Array.from({ length: cols }).map((_, j) => (
            <Skeleton key={j} variant="rectangular" height={28} sx={{ flex: j === 1 ? 3 : 1 }} />
          ))}
        </Stack>
      ))}
    </Stack>
  );
}

function mapTypeToKey(type: BcuItemType): string {
  switch (type) {
    case 'MO': return 'bcu-mao-obra';
    case 'EQP': return 'bcu-equipamentos';
    case 'ENC': return 'bcu-encargos';
    case 'EPI': return 'bcu-epi';
    case 'FER': return 'bcu-ferramentas';
    case 'MOB': return 'bcu-mobilizacao';
  }
}

// ── Tab config ───────────────────────────────────────────────────────────────

const TABS = [
  {
    id: 'mao-obra', label: 'Mão de Obra', icon: <EngineeringOutlinedIcon fontSize="small" />,
    help: 'Tabela de salários, categorias, produtividade e encargos de mão de obra utilizada nas composições.',
  },
  {
    id: 'equipamentos', label: 'Equipamentos', icon: <LocalShippingOutlinedIcon fontSize="small" />,
    help: 'Custo horário de equipamentos: aluguel, consumo de combustível e manutenção por hora trabalhada.',
  },
  {
    id: 'encargos', label: 'Encargos', icon: <WorkOutlineOutlinedIcon fontSize="small" />,
    help: 'Encargos sociais e trabalhistas (horistas e mensalistas) incidentes sobre a remuneração da mão de obra.',
  },
  {
    id: 'epi', label: 'EPI / Uniforme', icon: <SecurityOutlinedIcon fontSize="small" />,
    help: 'Custo de Equipamentos de Proteção Individual e uniformes por função, rateados mensalmente.',
  },
  {
    id: 'ferramentas', label: 'Ferramentas', icon: <HardwareOutlinedIcon fontSize="small" />,
    help: 'Custo de ferramentas e instrumentos necessários à execução dos serviços, rateado pelo tempo de vida útil.',
  },
  {
    id: 'mobilizacao', label: 'Mobilização', icon: <SafetyDividerOutlinedIcon fontSize="small" />,
    help: 'Custos de mobilização e desmobilização de equipes e equipamentos no início e encerramento da obra.',
  },
];

// ── Main Page ────────────────────────────────────────────────────────────────

export function BcuPage() {
  const [activeTab, setActiveTab] = useState(0);
  const { showMessage } = useFeedback();
  const queryClient = useQueryClient();

  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogType, setDialogType] = useState<BcuItemType>('MO');
  const [editingItem, setEditingItem] = useState<unknown | null>(null);
  const [editingItemId, setEditingItemId] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<{ type: BcuItemType; id: string } | null>(null);

  const { data: cabecalhos, isLoading: loadingCab, error: cabError } = useQuery({
    queryKey: ['bcu-cabecalhos'],
    queryFn: () => bcuApi.listCabecalhos(),
  });

  const cabecalho = cabecalhos?.find(c => c.is_ativo) ?? cabecalhos?.[0];

  const invalidate = (key: string) => {
    void queryClient.invalidateQueries({ queryKey: [key, cabecalho?.id] });
  };

  const handleCrudError = (err: unknown) => {
    const msg = extractApiErrorMessage(err, 'Erro na operação.');
    if (msg.includes('404') || msg.includes('Not Found') || msg.includes('Method Not Allowed')) {
      showMessage('Operação não disponível: endpoint backend ainda não implementado. Contratos TS prontos em bcuItemApi.ts.', 'error');
    } else {
      showMessage(msg, 'error');
    }
  };

  const criarMutation = useMutation({
    mutationFn: async ({ type, body }: { type: BcuItemType; body: unknown }) => {
      if (!cabecalho) throw new Error('Sem cabeçalho');
      switch (type) {
        case 'MO': return bcuItemApi.criarMaoObra(cabecalho.id, body as Parameters<typeof bcuItemApi.criarMaoObra>[1]);
        case 'EQP': return bcuItemApi.criarEquipamento(cabecalho.id, body as Parameters<typeof bcuItemApi.criarEquipamento>[1]);
        case 'ENC': return bcuItemApi.criarEncargo(cabecalho.id, body as Parameters<typeof bcuItemApi.criarEncargo>[1]);
        case 'EPI': return bcuItemApi.criarEpi(cabecalho.id, body as Parameters<typeof bcuItemApi.criarEpi>[1]);
        case 'FER': return bcuItemApi.criarFerramenta(cabecalho.id, body as Parameters<typeof bcuItemApi.criarFerramenta>[1]);
        case 'MOB': return bcuItemApi.criarMobilizacao(cabecalho.id, body as Parameters<typeof bcuItemApi.criarMobilizacao>[1]);
      }
    },
    onSuccess: (_, vars) => {
      setDialogOpen(false);
      setEditingItem(null);
      showMessage('Item criado com sucesso.');
      invalidate(mapTypeToKey(vars.type));
    },
    onError: handleCrudError,
  });

  const atualizarMutation = useMutation({
    mutationFn: async ({ type, id, body }: { type: BcuItemType; id: string; body: unknown }) => {
      if (!cabecalho) throw new Error('Sem cabeçalho');
      switch (type) {
        case 'MO': return bcuItemApi.atualizarMaoObra(cabecalho.id, id, body as Parameters<typeof bcuItemApi.atualizarMaoObra>[2]);
        case 'EQP': return bcuItemApi.atualizarEquipamento(cabecalho.id, id, body as Parameters<typeof bcuItemApi.atualizarEquipamento>[2]);
        case 'ENC': return bcuItemApi.atualizarEncargo(cabecalho.id, id, body as Parameters<typeof bcuItemApi.atualizarEncargo>[2]);
        case 'EPI': return bcuItemApi.atualizarEpi(cabecalho.id, id, body as Parameters<typeof bcuItemApi.atualizarEpi>[2]);
        case 'FER': return bcuItemApi.atualizarFerramenta(cabecalho.id, id, body as Parameters<typeof bcuItemApi.atualizarFerramenta>[2]);
        case 'MOB': return bcuItemApi.atualizarMobilizacao(cabecalho.id, id, body as Parameters<typeof bcuItemApi.atualizarMobilizacao>[2]);
      }
    },
    onSuccess: (_, vars) => {
      setDialogOpen(false);
      setEditingItem(null);
      setEditingItemId(null);
      showMessage('Item atualizado com sucesso.');
      invalidate(mapTypeToKey(vars.type));
    },
    onError: handleCrudError,
  });

  const deletarMutation = useMutation({
    mutationFn: async ({ type, id }: { type: BcuItemType; id: string }) => {
      if (!cabecalho) throw new Error('Sem cabeçalho');
      switch (type) {
        case 'MO': return bcuItemApi.deletarMaoObra(cabecalho.id, id);
        case 'EQP': return bcuItemApi.deletarEquipamento(cabecalho.id, id);
        case 'ENC': return bcuItemApi.deletarEncargo(cabecalho.id, id);
        case 'EPI': return bcuItemApi.deletarEpi(cabecalho.id, id);
        case 'FER': return bcuItemApi.deletarFerramenta(cabecalho.id, id);
        case 'MOB': return bcuItemApi.deletarMobilizacao(cabecalho.id, id);
      }
    },
    onSuccess: (_, vars) => {
      setDeleteConfirm(null);
      showMessage('Item removido com sucesso.');
      invalidate(mapTypeToKey(vars.type));
    },
    onError: (err) => {
      setDeleteConfirm(null);
      handleCrudError(err);
    },
  });

  const openEdit = (type: BcuItemType, item: unknown, id: string) => {
    setDialogType(type);
    setEditingItem(item);
    setEditingItemId(id);
    setDialogOpen(true);
  };

  return (
    <Box>
      <PageHeader
        title="Base de Custos Unitários"
        description="Dados base para composição de preços unitários: mão de obra, equipamentos, encargos, EPI e ferramentas."
      />

      {loadingCab && (
        <Stack spacing={1}>
          <Skeleton variant="rectangular" height={40} />
          <Skeleton variant="rectangular" height={300} />
        </Stack>
      )}

      {cabError && (
        <Alert severity="error">Erro ao carregar dados da BCU.</Alert>
      )}

      {!loadingCab && !cabError && !cabecalho && (
        <Alert severity="info" icon={<ConstructionOutlinedIcon />}>
          Nenhuma BCU importada. Acesse <strong>Governança → Upload</strong> para importar o arquivo <em>BCU tabelas.xlsx</em>.
        </Alert>
      )}

      {cabecalho && (
        <>
          <Paper variant="outlined" sx={{ mb: 2, px: 2, py: 1 }}>
            <Stack direction="row" spacing={3} alignItems="center" flexWrap="wrap">
              <Box>
                <Typography variant="caption" color="text.secondary">Arquivo</Typography>
                <Typography variant="body2" fontWeight={600}>{cabecalho.nome_arquivo}</Typography>
              </Box>
              {cabecalho.data_referencia && (
                <Box>
                  <Typography variant="caption" color="text.secondary">Data Referência</Typography>
                  <Typography variant="body2" fontWeight={600}>{cabecalho.data_referencia}</Typography>
                </Box>
              )}
              <Box>
                <Typography variant="caption" color="text.secondary">Importado em</Typography>
                <Typography variant="body2" fontWeight={600}>
                  {new Date(cabecalho.criado_em).toLocaleDateString('pt-BR')}
                </Typography>
              </Box>
              <Chip label={cabecalho.is_ativo ? 'Base ativa' : 'Inativa'} color={cabecalho.is_ativo ? 'success' : 'default'} size="small" />
            </Stack>
          </Paper>

          <Paper variant="outlined" sx={{ overflow: 'hidden' }}>
            <Tabs
              value={activeTab}
              onChange={(_, v) => setActiveTab(v)}
              variant="scrollable"
              scrollButtons="auto"
              sx={{
                borderBottom: 1,
                borderColor: 'divider',
                '& .MuiTab-root': { minHeight: 48, fontSize: '0.8rem' },
              }}
            >
              {TABS.map((tab) => (
                <Tab
                  key={tab.id}
                  icon={tab.icon}
                  iconPosition="start"
                  label={
                    <>
                      {tab.label}
                      <HelpTooltip title={tab.help} />
                    </>
                  }
                />
              ))}
            </Tabs>

            <Box sx={{ p: 0, overflowX: 'auto' }}>
              {activeTab === 0 && <MaoObraTab cabecalhoId={cabecalho.id} onEdit={(item) => openEdit('MO', item, item.id)} onDelete={(id) => setDeleteConfirm({ type: 'MO', id })} />}
              {activeTab === 1 && <EquipamentosTab cabecalhoId={cabecalho.id} onEdit={(item) => openEdit('EQP', item, item.id)} onDelete={(id) => setDeleteConfirm({ type: 'EQP', id })} />}
              {activeTab === 2 && <EncargosTab cabecalhoId={cabecalho.id} onEdit={(item) => openEdit('ENC', item, item.id)} onDelete={(id) => setDeleteConfirm({ type: 'ENC', id })} />}
              {activeTab === 3 && <EpiTab cabecalhoId={cabecalho.id} onEdit={(item) => openEdit('EPI', item, item.id)} onDelete={(id) => setDeleteConfirm({ type: 'EPI', id })} />}
              {activeTab === 4 && <FerramentasTab cabecalhoId={cabecalho.id} onEdit={(item) => openEdit('FER', item, item.id)} onDelete={(id) => setDeleteConfirm({ type: 'FER', id })} />}
              {activeTab === 5 && <MobilizacaoTab cabecalhoId={cabecalho.id} onEdit={(item) => openEdit('MOB', item, item.id)} onDelete={(id) => setDeleteConfirm({ type: 'MOB', id })} />}
            </Box>
          </Paper>
        </>
      )}

      <BcuItemDialog
        key={`${dialogType}-${editingItemId ?? 'new'}`}
        open={dialogOpen}
        type={dialogType}
        initial={editingItem ?? undefined}
        onClose={() => {
          setDialogOpen(false);
          setEditingItem(null);
          setEditingItemId(null);
        }}
        onSubmit={(body) => {
          if (editingItemId) {
            atualizarMutation.mutate({ type: dialogType, id: editingItemId, body });
          } else {
            criarMutation.mutate({ type: dialogType, body });
          }
        }}
      />

      <ConfirmationDialog
        open={!!deleteConfirm}
        title="Remover item"
        confirmLabel={deletarMutation.isPending ? 'Removendo…' : 'Remover'}
        confirmColor="error"
        isLoading={deletarMutation.isPending}
        onCancel={() => !deletarMutation.isPending && setDeleteConfirm(null)}
        onConfirm={() => deleteConfirm && deletarMutation.mutate(deleteConfirm)}
      >
        <Typography variant="body2">
          Confirma a exclusão permanente deste item?
        </Typography>
      </ConfirmationDialog>
    </Box>
  );
}
