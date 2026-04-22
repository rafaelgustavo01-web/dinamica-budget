import BuildCircleOutlinedIcon from '@mui/icons-material/BuildCircleOutlined';
import StorageOutlinedIcon from '@mui/icons-material/StorageOutlined';
import UploadFileOutlinedIcon from '@mui/icons-material/UploadFileOutlined';
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  FormControlLabel,
  Paper,
  Radio,
  RadioGroup,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useRef, useState } from 'react';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

import type { EtlExecuteRequest, EtlMode, EtlUploadResponse } from '../../shared/types/contracts/admin';
import {
  errorMessages,
  infoMessages,
  successMessages,
  warningMessages,
} from '../../shared/components/FeedbackMessages';
import { PageHeader } from '../../shared/components/PageHeader';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { adminApi } from '../../shared/services/api/adminApi';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';

export function AdminPage() {
  const { showMessage } = useFeedback();

  // ── Embeddings ─────────────────────────────────────────────────────────────
  const embeddingsMutation = useMutation({
    mutationFn: () => adminApi.computeEmbeddings(),
    onSuccess: () => {
      showMessage(successMessages.embeddingsProcessed);
    },
  });

  // ── ETL state ──────────────────────────────────────────────────────────────
  const [tcpoUpload, setTcpoUpload] = useState<EtlUploadResponse | null>(null);
  const [converterUpload, setConverterUpload] = useState<EtlUploadResponse | null>(null);
  const [etlMode, setEtlMode] = useState<EtlMode>('upsert');
  const [recomputarEmbeddings, setRecomputarEmbeddings] = useState(true);
  const tcpoInputRef = useRef<HTMLInputElement>(null);
  const converterInputRef = useRef<HTMLInputElement>(null);

  const tcpoMutation = useMutation({
    mutationFn: (file: File) => adminApi.uploadTcpo(file),
    onSuccess: (data) => {
      setTcpoUpload(data);
      showMessage(successMessages.etlUploaded);
    },
    onError: (err) => {
      showMessage(extractApiErrorMessage(err, errorMessages.etlUpload), 'error');
    },
  });

  const converterMutation = useMutation({
    mutationFn: (file: File) => adminApi.uploadConverter(file),
    onSuccess: (data) => {
      setConverterUpload(data);
      showMessage(successMessages.etlUploaded);
    },
    onError: (err) => {
      showMessage(extractApiErrorMessage(err, errorMessages.etlUpload), 'error');
    },
  });

  const executeMutation = useMutation({
    mutationFn: () => {
      const req: EtlExecuteRequest = {
        parse_token_tcpo: tcpoUpload?.parse_token,
        parse_token_converter: converterUpload?.parse_token,
        mode: etlMode,
        recomputar_embeddings: recomputarEmbeddings,
      };
      return adminApi.executeEtl(req);
    },
    onSuccess: () => {
      showMessage(successMessages.etlExecuted);
      setTcpoUpload(null);
      setConverterUpload(null);
      statusRefetch();
    },
    onError: (err) => {
      showMessage(extractApiErrorMessage(err, errorMessages.etlExecute), 'error');
    },
  });

  const { data: etlStatus, refetch: statusRefetch } = useQuery({
    queryKey: ['etl-status'],
    queryFn: () => adminApi.getEtlStatus(),
  });

  const canExecute = !!(tcpoUpload || converterUpload);

  return (
    <>
      <PageHeader
        title="Administração"
        description="Configurações avançadas do sistema. Área restrita a administradores."
      />

      <Stack spacing={3}>
        {/* ── Embeddings ─────────────────────────────────────────────────── */}
        <Paper sx={{ p: 3, border: '1px solid', borderColor: 'divider' }}>
          <Stack spacing={2}>
            <Stack direction="row" spacing={1.5} alignItems="center">
              <BuildCircleOutlinedIcon color="primary" />
              <Typography variant="h6">Processamento de embeddings</Typography>
            </Stack>
            <Typography variant="body2" color="text.secondary">
              Recalcula os vetores de similaridade semântica do catálogo de serviços.
              Execute após atualizações relevantes no banco TCPO.
            </Typography>
            <Alert severity="info">{infoMessages.processing}</Alert>
            <Button
              variant="contained"
              onClick={() => embeddingsMutation.mutate()}
              disabled={embeddingsMutation.isPending}
              sx={{ alignSelf: 'flex-start' }}
            >
              {embeddingsMutation.isPending ? (
                <CircularProgress size={20} color="inherit" />
              ) : (
                'Processar embeddings'
              )}
            </Button>
            {embeddingsMutation.data ? (
              <Alert severity="success">
                Resultado: {embeddingsMutation.data.embeddings_computados} itens processados.
              </Alert>
            ) : null}
            {embeddingsMutation.isError ? (
              <Alert severity="error">
                {extractApiErrorMessage(embeddingsMutation.error, errorMessages.embeddings)}
              </Alert>
            ) : null}
          </Stack>
        </Paper>

        {/* ── ETL ────────────────────────────────────────────────────────── */}
        <Paper sx={{ p: 3, border: '1px solid', borderColor: 'divider' }}>
          <Stack spacing={3}>
            <Stack direction="row" spacing={1.5} alignItems="center">
              <StorageOutlinedIcon color="primary" />
              <Typography variant="h6">Carga ETL — Base TCPO</Typography>
            </Stack>

            {/* Status row */}
            {etlStatus && (
              <Stack direction="row" spacing={2} flexWrap="wrap">
                <Chip label={`${etlStatus.total_itens_base_tcpo.toLocaleString()} itens base`} size="small" />
                <Chip label={`${etlStatus.total_composicoes_base.toLocaleString()} relações BOM`} size="small" />
                <Chip label={`${etlStatus.total_embeddings.toLocaleString()} embeddings`} size="small" />
                {etlStatus.ultima_carga && (
                  <Chip
                    label={`Última carga: ${new Date(etlStatus.ultima_carga).toLocaleDateString('pt-BR')}`}
                    size="small"
                    variant="outlined"
                  />
                )}
              </Stack>
            )}

            <Divider />

            {/* Upload buttons */}
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              {/* TCPO */}
              <Box sx={{ flex: 1 }}>
                <input
                  ref={tcpoInputRef}
                  type="file"
                  accept=".xlsx,.xls"
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) tcpoMutation.mutate(file);
                    e.target.value = '';
                  }}
                />
                <Button
                  variant="outlined"
                  fullWidth
                  startIcon={<UploadFileOutlinedIcon />}
                  onClick={() => tcpoInputRef.current?.click()}
                  disabled={tcpoMutation.isPending}
                >
                  {tcpoMutation.isPending ? (
                    <CircularProgress size={18} color="inherit" />
                  ) : (
                    'Upload — Composições TCPO - PINI.xlsx'
                  )}
                </Button>
                {tcpoUpload && (
                  <Chip
                    sx={{ mt: 1 }}
                    label={`${tcpoUpload.parse_preview.total_itens.toLocaleString()} itens · ${tcpoUpload.parse_preview.total_relacoes.toLocaleString()} relações`}
                    color="success"
                    size="small"
                  />
                )}
              </Box>

              {/* Converter */}
              <Box sx={{ flex: 1 }}>
                <input
                  ref={converterInputRef}
                  type="file"
                  accept=".xlsx,.xls"
                  style={{ display: 'none' }}
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) converterMutation.mutate(file);
                    e.target.value = '';
                  }}
                />
                <Button
                  variant="outlined"
                  fullWidth
                  startIcon={<UploadFileOutlinedIcon />}
                  onClick={() => converterInputRef.current?.click()}
                  disabled={converterMutation.isPending}
                >
                  {converterMutation.isPending ? (
                    <CircularProgress size={18} color="inherit" />
                  ) : (
                    'Upload — Converter em Data Center.xlsx'
                  )}
                </Button>
                {converterUpload && (
                  <Chip
                    sx={{ mt: 1 }}
                    label={`${converterUpload.parse_preview.total_itens.toLocaleString()} itens auxiliares`}
                    color="success"
                    size="small"
                  />
                )}
              </Box>
            </Stack>

            {/* Preview accordions */}
            {tcpoUpload && (
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="body2">
                    Prévia TCPO — {tcpoUpload.parse_preview.total_itens.toLocaleString()} itens
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Código</TableCell>
                        <TableCell>Descrição</TableCell>
                        <TableCell>Unidade</TableCell>
                        <TableCell align="right">Custo base</TableCell>
                        <TableCell>Tipo</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {tcpoUpload.parse_preview.itens_amostra.map((item) => (
                        <TableRow key={item.codigo_origem}>
                          <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                            {item.codigo_origem}
                          </TableCell>
                          <TableCell>{item.descricao}</TableCell>
                          <TableCell>{item.unidade_medida}</TableCell>
                          <TableCell align="right">
                            {item.custo_base.toLocaleString('pt-BR', {
                              style: 'currency',
                              currency: 'BRL',
                            })}
                          </TableCell>
                          <TableCell>
                            <Chip label={item.tipo_recurso ?? '—'} size="small" />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  {tcpoUpload.parse_preview.avisos.length > 0 && (
                    <Alert severity="warning" sx={{ mt: 1 }}>
                      {tcpoUpload.parse_preview.avisos.slice(0, 5).join(' | ')}
                    </Alert>
                  )}
                </AccordionDetails>
              </Accordion>
            )}

            {/* Mode + execute */}
            {canExecute && (
              <>
                <Divider />
                <Stack spacing={1.5}>
                  <Typography variant="subtitle2">Modo de carga</Typography>
                  <RadioGroup
                    row
                    value={etlMode}
                    onChange={(_, v) => setEtlMode(v as EtlMode)}
                  >
                    <FormControlLabel
                      value="upsert"
                      control={<Radio size="small" />}
                      label="Incrementar (UPSERT)"
                    />
                    <FormControlLabel
                      value="replace"
                      control={<Radio size="small" />}
                      label="Substituir (REPLACE)"
                    />
                  </RadioGroup>
                  {etlMode === 'replace' && (
                    <Alert severity="warning">{warningMessages.etlReplaceMode}</Alert>
                  )}
                  <FormControlLabel
                    control={
                      <Radio
                        size="small"
                        checked={recomputarEmbeddings}
                        onChange={(_, v) => setRecomputarEmbeddings(v)}
                      />
                    }
                    label="Recomputar embeddings após carga"
                  />
                </Stack>

                <Button
                  variant="contained"
                  color="primary"
                  onClick={() => executeMutation.mutate()}
                  disabled={executeMutation.isPending}
                  sx={{ alignSelf: 'flex-start' }}
                >
                  {executeMutation.isPending ? (
                    <>
                      <CircularProgress size={18} color="inherit" sx={{ mr: 1 }} />
                      {infoMessages.etlProcessing}
                    </>
                  ) : (
                    'Executar carga ETL'
                  )}
                </Button>

                {executeMutation.data && (
                  <Alert severity="success">
                    Inseridos: {executeMutation.data.itens_inseridos.toLocaleString()} ·{' '}
                    Atualizados: {executeMutation.data.itens_atualizados.toLocaleString()} ·{' '}
                    Relações: {executeMutation.data.relacoes_inseridas.toLocaleString()} ·{' '}
                    Duração: {executeMutation.data.duracao_segundos}s
                  </Alert>
                )}
                {executeMutation.isError && (
                  <Alert severity="error">
                    {extractApiErrorMessage(executeMutation.error, errorMessages.etlExecute)}
                  </Alert>
                )}
              </>
            )}
          </Stack>
        </Paper>
      </Stack>
    </>
  );
}
