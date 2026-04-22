import DownloadOutlinedIcon from '@mui/icons-material/DownloadOutlined';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import TableViewOutlinedIcon from '@mui/icons-material/TableViewOutlined';
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Autocomplete,
  Box,
  Chip,
  CircularProgress,
  Divider,
  IconButton,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import {
  errorMessages,
  infoMessages,
} from '../../shared/components/FeedbackMessages';
import { PageHeader } from '../../shared/components/PageHeader';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { clientsApi } from '../../shared/services/api/clientsApi';
import { extractionApi } from '../../shared/services/api/extractionApi';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import type { ClienteResponse } from '../../shared/types/contracts/clientes';
import type { ServicoClienteAssociado } from '../../shared/types/contracts/extraction';
import type { ExplodeComposicaoResponse } from '../../shared/types/contracts/servicos';
import { formatCurrency, formatNumber } from '../../shared/utils/format';
import { useAuth } from '../auth/AuthProvider';

function TipoChip({ tipo }: { tipo: string | null }) {
  const colorMap: Record<string, 'primary' | 'secondary' | 'default' | 'info' | 'warning'> = {
    MO: 'primary',
    INSUMO: 'default',
    EQUIPAMENTO: 'warning',
    FERRAMENTA: 'info',
    SERVICO: 'secondary',
  };
  return (
    <Chip
      label={tipo ?? '—'}
      size="small"
      color={tipo ? colorMap[tipo] ?? 'default' : 'default'}
      variant="outlined"
    />
  );
}

function BomAccordion({
  servico,
  clienteId,
}: {
  servico: ServicoClienteAssociado;
  clienteId: string;
}) {
  const { showMessage } = useFeedback();
  const [expanded, setExpanded] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const bomQuery = useQuery<ExplodeComposicaoResponse>({
    queryKey: ['bom', servico.item_referencia_id, clienteId],
    queryFn: () => extractionApi.getDadosBrutos(servico.item_referencia_id, clienteId),
    enabled: expanded,
  });

  const handleDownload = async () => {
    setDownloading(true);
    try {
      await extractionApi.downloadXlsx(servico.item_referencia_id, clienteId);
    } catch (err) {
      showMessage(extractApiErrorMessage(err, errorMessages.xlsxDownload), 'error');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <Accordion
      expanded={expanded}
      onChange={(_, v) => setExpanded(v)}
      sx={{ border: '1px solid', borderColor: 'divider', '&:before': { display: 'none' } }}
    >
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack direction="row" spacing={2} alignItems="center" sx={{ flex: 1, pr: 1 }}>
          <Typography
            variant="body2"
            sx={{ fontFamily: 'monospace', minWidth: 120, color: 'text.secondary' }}
          >
            {servico.codigo_origem}
          </Typography>
          <Typography variant="body2" sx={{ flex: 1 }}>
            {servico.descricao_cliente}
          </Typography>
          <TipoChip tipo={servico.tipo_recurso} />
          <Typography variant="body2" sx={{ minWidth: 60, textAlign: 'right', color: 'text.secondary' }}>
            {servico.unidade_medida}
          </Typography>
          <Tooltip title="Baixar BOM (.xlsx)">
            <span>
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDownload();
                }}
                disabled={downloading}
              >
                {downloading ? (
                  <CircularProgress size={16} />
                ) : (
                  <DownloadOutlinedIcon fontSize="small" />
                )}
              </IconButton>
            </span>
          </Tooltip>
        </Stack>
      </AccordionSummary>

      <AccordionDetails sx={{ p: 0 }}>
        {bomQuery.isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
            <CircularProgress size={24} />
          </Box>
        )}
        {bomQuery.isError && (
          <Alert severity="error" sx={{ m: 2 }}>
            {extractApiErrorMessage(bomQuery.error, errorMessages.extractionExplode)}
          </Alert>
        )}
        {bomQuery.data && (
          <>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Código</TableCell>
                  <TableCell>Descrição</TableCell>
                  <TableCell>Unidade</TableCell>
                  <TableCell align="right">Qtd</TableCell>
                  <TableCell align="right">Custo Unit.</TableCell>
                  <TableCell align="right">Custo Total</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {bomQuery.data.itens.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                      {item.insumo_filho_id.slice(0, 8)}…
                    </TableCell>
                    <TableCell>{item.descricao_filho}</TableCell>
                    <TableCell>{item.unidade_medida}</TableCell>
                    <TableCell align="right">
                      {formatNumber(Number(item.quantidade_consumo))}
                    </TableCell>
                    <TableCell align="right">
                      {formatCurrency(Number(item.custo_unitario))}
                    </TableCell>
                    <TableCell align="right">
                      {formatCurrency(Number(item.custo_total))}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <Stack
              direction="row"
              justifyContent="flex-end"
              sx={{ p: 1.5, borderTop: '1px solid', borderColor: 'divider' }}
            >
              <Typography variant="subtitle2">
                Total BOM:{' '}
                <strong>
                  {formatCurrency(Number(bomQuery.data.custo_total_composicao))}
                </strong>
              </Typography>
            </Stack>
          </>
        )}
      </AccordionDetails>
    </Accordion>
  );
}

export function ExtractionPage() {
  const { user, selectedClientId: globalClientId } = useAuth();
  const [selectedCliente, setSelectedCliente] = useState<ClienteResponse | null>(null);
  const [clienteInputValue, setClienteInputValue] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [page] = useState(1);

  // For admins: let them pick any client. For regular users: only their clients.
  const clientesQuery = useQuery({
    queryKey: ['clientes-list', clienteInputValue],
    queryFn: () =>
      clientsApi.list({ is_active: true, page: 1, page_size: 50 }),
    enabled: user?.is_admin === true,
  });

  // If not admin, resolve client from their selected context
  const effectiveClienteId =
    user?.is_admin === true
      ? selectedCliente?.id ?? ''
      : globalClientId;

  const servicosQuery = useQuery({
    queryKey: ['servicos-cliente', effectiveClienteId, searchQuery, page],
    queryFn: () =>
      extractionApi.getServicosCliente({
        cliente_id: effectiveClienteId,
        q: searchQuery || undefined,
        page,
        page_size: 20,
      }),
    enabled: Boolean(effectiveClienteId),
  });

  const clienteOptions: ClienteResponse[] = clientesQuery.data?.items ?? [];

  return (
    <>
      <PageHeader
        title="Extração PC"
        description="Selecione um cliente e explore os serviços associados. Baixe o BOM de qualquer composição."
      />

      <Stack spacing={3}>
        {/* ── Context selector ─────────────────────────────────────── */}
        <Paper sx={{ p: 3, border: '1px solid', borderColor: 'divider' }}>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} alignItems="flex-start">
            <TableViewOutlinedIcon color="primary" sx={{ mt: 0.5 }} />

            {user?.is_admin === true ? (
              <Autocomplete
                sx={{ minWidth: 320 }}
                options={clienteOptions}
                getOptionLabel={(o) => `${o.nome_fantasia} (${o.cnpj})`}
                value={selectedCliente}
                inputValue={clienteInputValue}
                onInputChange={(_, v) => setClienteInputValue(v)}
                onChange={(_, v) => setSelectedCliente(v)}
                renderInput={(params) => (
                  <TextField {...params} label="Cliente (contexto)" size="small" />
                )}
                loading={clientesQuery.isLoading}
                noOptionsText="Nenhum cliente encontrado"
              />
            ) : (
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Contexto ativo:{' '}
                  <strong>{globalClientId ? globalClientId : '— selecione um cliente no topo da tela'}</strong>
                </Typography>
              </Box>
            )}

            <TextField
              label="Buscar por descrição do cliente"
              size="small"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={infoMessages.extractionSearching}
              sx={{ minWidth: 280, flex: 1 }}
            />
          </Stack>
        </Paper>

        {/* ── Results ──────────────────────────────────────────────── */}
        {!effectiveClienteId && (
          <Alert severity="info">Selecione um cliente para ver os serviços associados.</Alert>
        )}

        {servicosQuery.isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {servicosQuery.isError && (
          <Alert severity="error">
            {extractApiErrorMessage(servicosQuery.error, errorMessages.extractionLoad)}
          </Alert>
        )}

        {servicosQuery.data && (
          <Paper sx={{ p: 0, border: '1px solid', borderColor: 'divider', overflow: 'hidden' }}>
            <Stack
              direction="row"
              justifyContent="space-between"
              alignItems="center"
              sx={{ px: 3, py: 2 }}
            >
              <Typography variant="subtitle1">
                {servicosQuery.data.total.toLocaleString()} serviço(s) associado(s)
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Clique em um serviço para ver e baixar o BOM
              </Typography>
            </Stack>

            <Divider />

            {servicosQuery.data.items.length === 0 ? (
              <Box sx={{ px: 3, py: 4 }}>
                <Typography color="text.secondary" align="center">
                  Nenhum serviço encontrado para os critérios informados.
                </Typography>
              </Box>
            ) : (
              <Stack spacing={0}>
                {servicosQuery.data.items.map((servico) => (
                  <BomAccordion
                    key={servico.id}
                    servico={servico}
                    clienteId={effectiveClienteId}
                  />
                ))}
              </Stack>
            )}
          </Paper>
        )}
      </Stack>
    </>
  );
}
