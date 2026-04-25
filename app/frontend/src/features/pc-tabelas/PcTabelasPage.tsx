import ConstructionOutlinedIcon from '@mui/icons-material/ConstructionOutlined';
import EngineeringOutlinedIcon from '@mui/icons-material/EngineeringOutlined';
import HardwareOutlinedIcon from '@mui/icons-material/HardwareOutlined';
import LocalShippingOutlinedIcon from '@mui/icons-material/LocalShippingOutlined';
import SafetyDividerOutlinedIcon from '@mui/icons-material/SafetyDividerOutlined';
import SecurityOutlinedIcon from '@mui/icons-material/SecurityOutlined';
import WorkOutlineOutlinedIcon from '@mui/icons-material/WorkOutlineOutlined';
import {
  Alert,
  Box,
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
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import { PageHeader } from '../../shared/components/PageHeader';
import type {
  PcEncargoItem,
  PcEquipamentoItem,
  PcEpiItem,
  PcFerramentaItem,
  PcMaoObraItem,
  PcMobilizacaoItem,
} from '../../shared/services/api/pcTabelasApi';
import { pcTabelasApi } from '../../shared/services/api/pcTabelasApi';

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

function MaoObraTab({ cabecalhoId }: { cabecalhoId: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['pc-mao-obra', cabecalhoId],
    queryFn: () => pcTabelasApi.getMaoObra(cabecalhoId),
  });

  if (isLoading) return <TableSkeleton rows={12} cols={8} />;
  if (error || !data) return <Alert severity="error">Erro ao carregar mão de obra.</Alert>;

  return (
    <TableContainer>
      <Table size="small" stickyHeader>
        <TableHead>
          <TableRow>
            <TableCell sx={headCell}>Função</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right' }}>Qtd</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right' }}>Salário</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right' }}>Reajuste</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right' }}>Encargos %</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right' }}>Refeição</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right' }}>Vale Alim.</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right' }}>Plano Saúde</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right' }}>EPI (R$)</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right' }}>Uniforme</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right' }}>Seguro Vida</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right' }}>Custo/H (R$)</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right' }}>Custo Mensal</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right' }}>Mobilização</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((item: PcMaoObraItem) => (
            <TableRow key={item.id} hover>
              <TableCell sx={dataCell}>
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
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

function EquipamentosTab({ cabecalhoId }: { cabecalhoId: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['pc-equipamentos', cabecalhoId],
    queryFn: () => pcTabelasApi.getEquipamentos(cabecalhoId),
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
            </TableRow>
          </TableHead>
          <TableBody>
            {data.items.map((item: PcEquipamentoItem) => (
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
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Stack>
  );
}

function EncargosTab({ cabecalhoId, tipo }: { cabecalhoId: string; tipo: 'HORISTA' | 'MENSALISTA' }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['pc-encargos', cabecalhoId, tipo],
    queryFn: () => pcTabelasApi.getEncargos(cabecalhoId, tipo),
  });

  if (isLoading) return <TableSkeleton rows={20} cols={4} />;
  if (error || !data) return <Alert severity="error">Erro ao carregar encargos.</Alert>;

  return (
    <TableContainer>
      <Table size="small" stickyHeader>
        <TableHead>
          <TableRow>
            <TableCell sx={headCell}>Grupo</TableCell>
            <TableCell sx={headCell}>Código</TableCell>
            <TableCell sx={headCell}>Discriminação</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right' }}>Taxa %</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((item: PcEncargoItem) => (
            <TableRow key={item.id} hover>
              <TableCell sx={dataCell}>
                {item.grupo && <Chip label={item.grupo} size="small" color="primary" variant="outlined" />}
              </TableCell>
              <TableCell sx={dataCell}>{item.codigo_grupo ?? '—'}</TableCell>
              <TableCell sx={dataCell}>{item.discriminacao_encargo}</TableCell>
              <TableCell sx={numCell}>{fmtPct(item.taxa_percent)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

function EpiTab({ cabecalhoId }: { cabecalhoId: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['pc-epi', cabecalhoId],
    queryFn: () => pcTabelasApi.getEpi(cabecalhoId),
  });

  if (isLoading) return <TableSkeleton rows={15} cols={6} />;
  if (error || !data) return <Alert severity="error">Erro ao carregar EPI.</Alert>;

  return (
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
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((item: PcEpiItem) => (
            <TableRow key={item.id} hover>
              <TableCell sx={dataCell}>
                <Typography variant="body2" fontWeight={500}>{item.epi}</Typography>
              </TableCell>
              <TableCell sx={dataCell}>{item.unidade ?? '—'}</TableCell>
              <TableCell sx={numCell}>R$ {fmt(item.custo_unitario)}</TableCell>
              <TableCell sx={numCell}>{fmt(item.quantidade, 1)}</TableCell>
              <TableCell sx={numCell}>{fmt(item.vida_util_meses, 0)} meses</TableCell>
              <TableCell sx={{ ...numCell, fontWeight: 600, color: 'primary.main' }}>R$ {fmt(item.custo_epi_mes)}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

function FerramentasTab({ cabecalhoId }: { cabecalhoId: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['pc-ferramentas', cabecalhoId],
    queryFn: () => pcTabelasApi.getFerramentas(cabecalhoId),
  });

  if (isLoading) return <TableSkeleton rows={20} cols={5} />;
  if (error || !data) return <Alert severity="error">Erro ao carregar ferramentas.</Alert>;

  const total = data.reduce((s: number, i: PcFerramentaItem) => s + (i.preco_total ?? 0), 0);

  return (
    <Stack spacing={2}>
      <TableContainer>
        <Table size="small" stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell sx={headCell}>Item</TableCell>
              <TableCell sx={headCell}>Descrição</TableCell>
              <TableCell sx={headCell}>Unid.</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Qtd</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Preço Unit.</TableCell>
              <TableCell sx={{ ...headCell, textAlign: 'right' }}>Total</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((item: PcFerramentaItem) => (
              <TableRow key={item.id} hover>
                <TableCell sx={dataCell}>{item.item ?? '—'}</TableCell>
                <TableCell sx={dataCell}>{item.descricao}</TableCell>
                <TableCell sx={dataCell}>{item.unidade ?? '—'}</TableCell>
                <TableCell sx={numCell}>{fmt(item.quantidade, 0)}</TableCell>
                <TableCell sx={numCell}>R$ {fmt(item.preco)}</TableCell>
                <TableCell sx={{ ...numCell, fontWeight: 600 }}>R$ {fmt(item.preco_total)}</TableCell>
              </TableRow>
            ))}
            <TableRow>
              <TableCell colSpan={5} sx={{ ...dataCell, fontWeight: 700, textAlign: 'right' }}>TOTAL</TableCell>
              <TableCell sx={{ ...numCell, fontWeight: 700, color: 'primary.main' }}>R$ {fmt(total)}</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    </Stack>
  );
}

function MobilizacaoTab({ cabecalhoId }: { cabecalhoId: string }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['pc-mobilizacao', cabecalhoId],
    queryFn: () => pcTabelasApi.getMobilizacao(cabecalhoId),
  });

  if (isLoading) return <TableSkeleton rows={10} cols={6} />;
  if (error || !data) return <Alert severity="error">Erro ao carregar mobilização.</Alert>;

  // Get all unique function columns
  const funcaoCols = Array.from(
    new Set(data.flatMap((i: PcMobilizacaoItem) => i.quantidades_funcao.map((q) => q.coluna_funcao)))
  );

  return (
    <TableContainer>
      <Table size="small" stickyHeader>
        <TableHead>
          <TableRow>
            <TableCell sx={headCell}>Exame / Evento</TableCell>
            <TableCell sx={{ ...headCell, textAlign: 'right' }}>Valor Unit.</TableCell>
            {funcaoCols.map((col) => (
              <TableCell key={col} sx={{ ...headCell, textAlign: 'right' }}>{col}</TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {data.map((item: PcMobilizacaoItem) => {
            const qMap = new Map(item.quantidades_funcao.map((q) => [q.coluna_funcao, q.quantidade]));
            return (
              <TableRow key={item.id} hover>
                <TableCell sx={dataCell}>{item.descricao}</TableCell>
                <TableCell sx={numCell}>{fmt(item.funcao ? parseFloat(item.funcao) : null)}</TableCell>
                {funcaoCols.map((col) => (
                  <TableCell key={col} sx={numCell}>R$ {fmt(qMap.get(col) ?? null)}</TableCell>
                ))}
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
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

// ── Tab config ───────────────────────────────────────────────────────────────

const TABS = [
  { id: 'mao-obra', label: 'Mão de Obra', icon: <EngineeringOutlinedIcon fontSize="small" /> },
  { id: 'equipamentos', label: 'Equipamentos', icon: <LocalShippingOutlinedIcon fontSize="small" /> },
  { id: 'encargos-horista', label: 'Encargos Horista', icon: <WorkOutlineOutlinedIcon fontSize="small" /> },
  { id: 'encargos-mensalista', label: 'Encargos Mensalista', icon: <WorkOutlineOutlinedIcon fontSize="small" /> },
  { id: 'epi', label: 'EPI / Uniforme', icon: <SecurityOutlinedIcon fontSize="small" /> },
  { id: 'ferramentas', label: 'Ferramentas', icon: <HardwareOutlinedIcon fontSize="small" /> },
  { id: 'mobilizacao', label: 'Mobilização', icon: <SafetyDividerOutlinedIcon fontSize="small" /> },
];

// ── Main Page ────────────────────────────────────────────────────────────────

export function PcTabelasPage() {
  const [activeTab, setActiveTab] = useState(0);

  const { data: cabecalhos, isLoading: loadingCab, error: cabError } = useQuery({
    queryKey: ['pc-cabecalhos'],
    queryFn: () => pcTabelasApi.listCabecalhos(),
  });

  const cabecalho = cabecalhos?.[0];

  return (
    <Box>
      <PageHeader
        title="PC Tabelas"
        description="Dados base para composição de preços unitários: mão de obra, equipamentos, encargos, EPI e ferramentas."
      />

      {loadingCab && (
        <Stack spacing={1}>
          <Skeleton variant="rectangular" height={40} />
          <Skeleton variant="rectangular" height={300} />
        </Stack>
      )}

      {cabError && (
        <Alert severity="error">Erro ao carregar dados das PC Tabelas.</Alert>
      )}

      {!loadingCab && !cabError && !cabecalho && (
        <Alert severity="info" icon={<ConstructionOutlinedIcon />}>
          Nenhuma PC Tabela importada. Acesse <strong>Governança → Upload</strong> para importar o arquivo <em>PC tabelas.xlsx</em>.
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
              <Chip label="Base ativa" color="success" size="small" />
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
                <Tab key={tab.id} label={tab.label} icon={tab.icon} iconPosition="start" />
              ))}
            </Tabs>

            <Box sx={{ p: 0, overflowX: 'auto' }}>
              {activeTab === 0 && <MaoObraTab cabecalhoId={cabecalho.id} />}
              {activeTab === 1 && <EquipamentosTab cabecalhoId={cabecalho.id} />}
              {activeTab === 2 && <EncargosTab cabecalhoId={cabecalho.id} tipo="HORISTA" />}
              {activeTab === 3 && <EncargosTab cabecalhoId={cabecalho.id} tipo="MENSALISTA" />}
              {activeTab === 4 && <EpiTab cabecalhoId={cabecalho.id} />}
              {activeTab === 5 && <FerramentasTab cabecalhoId={cabecalho.id} />}
              {activeTab === 6 && <MobilizacaoTab cabecalhoId={cabecalho.id} />}
            </Box>
          </Paper>
        </>
      )}
    </Box>
  );
}
