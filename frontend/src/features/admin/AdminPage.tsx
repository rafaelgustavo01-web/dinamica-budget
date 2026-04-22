import BuildCircleOutlinedIcon from '@mui/icons-material/BuildCircleOutlined';
<<<<<<< HEAD
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
=======
import CloudUploadOutlinedIcon from '@mui/icons-material/CloudUploadOutlined';
import PreviewOutlinedIcon from '@mui/icons-material/PreviewOutlined';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  FormControl,
  InputLabel,
  LinearProgress,
  MenuItem,
  Paper,
  Select,
>>>>>>> 5f0973541797732f99516ee792729f7f3cef10c2
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
<<<<<<< HEAD
import { useMutation, useQuery } from '@tanstack/react-query';
import { useRef, useState } from 'react';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

import type { EtlExecuteRequest, EtlMode, EtlUploadResponse } from '../../shared/types/contracts/admin';
=======
import { useMutation } from '@tanstack/react-query';
import { useMemo, useState } from 'react';

import { ConfirmationDialog } from '../../shared/components/ConfirmationDialog';
>>>>>>> 5f0973541797732f99516ee792729f7f3cef10c2
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
import type { ImportPreviewResponse, ImportSourceType } from '../../shared/types/contracts/admin';

export function AdminPage() {
  const { showMessage } = useFeedback();
  const [sourceType, setSourceType] = useState<ImportSourceType>('TCPO');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);

  // ── Embeddings ─────────────────────────────────────────────────────────────
  const embeddingsMutation = useMutation({
    mutationFn: () => adminApi.computeEmbeddings(),
    onSuccess: () => {
      showMessage(successMessages.embeddingsProcessed);
    },
  });

<<<<<<< HEAD
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
=======
  const previewMutation = useMutation({
    mutationFn: (params: { file: File; sourceType: ImportSourceType }) =>
      adminApi.previewImport(params.file, params.sourceType),
    onSuccess: (data) => {
      setPreview(data);
      showMessage('Preview gerado com sucesso. Revise os mapeamentos antes de confirmar a carga.');
>>>>>>> 5f0973541797732f99516ee792729f7f3cef10c2
    },
  });

  const executeMutation = useMutation({
<<<<<<< HEAD
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
=======
    mutationFn: (params: { file: File; sourceType: ImportSourceType }) =>
      adminApi.executeImport(params.file, params.sourceType, true),
    onSuccess: (data) => {
      setConfirmOpen(false);
      showMessage(data.message);
    },
  });

  const confidenceAvg = useMemo(() => {
    if (!preview) {
      return 0;
    }
    const all = preview.sheets.flatMap((sheet) => sheet.mapped_fields);
    if (!all.length) {
      return 0;
    }
    return all.reduce((acc, item) => acc + item.confidence, 0) / all.length;
  }, [preview]);

  const handlePreview = () => {
    if (!selectedFile) {
      showMessage('Selecione um arquivo .xlsx antes de gerar o preview.', 'warning');
      return;
    }
    previewMutation.mutate({ file: selectedFile, sourceType });
  };

  const handleExecute = () => {
    if (!selectedFile) {
      showMessage('Selecione um arquivo .xlsx para executar a carga.', 'warning');
      return;
    }
    executeMutation.mutate({ file: selectedFile, sourceType });
  };
>>>>>>> 5f0973541797732f99516ee792729f7f3cef10c2

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

<<<<<<< HEAD
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
=======
        <Paper
          sx={{
            flex: 1,
            p: 3,
            border: '1px solid',
            borderColor: 'divider',
            background: 'linear-gradient(145deg, rgba(20,95,185,0.06), rgba(227,181,5,0.05))',
          }}
        >
          <Stack spacing={2.5}>
            <Stack direction="row" spacing={1.5} alignItems="center">
              <CloudUploadOutlinedIcon color="primary" />
              <Typography variant="h6">Carga inteligente da base de consulta</Typography>
            </Stack>

            <Typography variant="body2" color="text.secondary">
              Faça upload da planilha, valide o mapeamento automático e confirme a execução.
              A carga só é iniciada após confirmação explícita.
            </Typography>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
              <FormControl fullWidth size="small">
                <InputLabel id="source-type-label">Tipo da base</InputLabel>
                <Select
                  labelId="source-type-label"
                  value={sourceType}
                  label="Tipo da base"
                  onChange={(event) => {
                    setSourceType(event.target.value as ImportSourceType);
                    setPreview(null);
                  }}
                >
                  <MenuItem value="TCPO">TCPO (composições oficiais)</MenuItem>
                  <MenuItem value="PC">PC (premissas e tabelas de custo)</MenuItem>
                </Select>
              </FormControl>

              <Button
                component="label"
                variant="outlined"
                sx={{ minWidth: { md: 220 } }}
              >
                {selectedFile ? selectedFile.name : 'Selecionar arquivo .xlsx'}
                <input
                  hidden
                  type="file"
                  accept=".xlsx"
                  onChange={(event) => {
                    const file = event.target.files?.[0] ?? null;
                    setSelectedFile(file);
                    setPreview(null);
                  }}
                />
              </Button>
            </Stack>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
              <Button
                variant="contained"
                startIcon={<PreviewOutlinedIcon />}
                disabled={previewMutation.isPending || !selectedFile}
                onClick={handlePreview}
              >
                {previewMutation.isPending ? 'Gerando preview...' : 'Gerar preview'}
              </Button>

              <Button
                color="warning"
                variant="contained"
                disabled={!preview || executeMutation.isPending}
                onClick={() => setConfirmOpen(true)}
              >
                {executeMutation.isPending ? 'Executando carga...' : 'Executar carga no banco'}
              </Button>
            </Stack>

            {previewMutation.isError ? (
              <Alert severity="error">
                {extractApiErrorMessage(previewMutation.error, 'Falha ao gerar preview da planilha.')}
              </Alert>
            ) : null}

            {executeMutation.isError ? (
              <Alert severity="error">
                {extractApiErrorMessage(executeMutation.error, 'Falha na execução da carga ETL.')}
              </Alert>
            ) : null}

            {preview ? (
              <Stack spacing={1.5}>
                <Alert severity="success">
                  Preview pronto para {preview.file_name}. Estimativa: {preview.estimated_records} registros.
                </Alert>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Confiança média de mapeamento: {(confidenceAvg * 100).toFixed(1)}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={Math.max(5, Math.round(confidenceAvg * 100))}
                    sx={{ mt: 0.75, borderRadius: 999 }}
                  />
                </Box>

                {preview.warnings.length ? (
                  <Alert severity="warning">
                    {preview.warnings.join(' | ')}
                  </Alert>
                ) : null}

                <Table size="small" sx={{ border: '1px solid', borderColor: 'divider' }}>
                  <TableHead>
                    <TableRow>
                      <TableCell>Aba</TableCell>
                      <TableCell>Linhas</TableCell>
                      <TableCell>Estimativa</TableCell>
                      <TableCell>Campos mapeados</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {preview.sheets.map((sheet) => (
                      <TableRow key={sheet.sheet_name}>
                        <TableCell>{sheet.sheet_name}</TableCell>
                        <TableCell>{sheet.total_rows}</TableCell>
                        <TableCell>{sheet.estimated_records}</TableCell>
                        <TableCell>
                          {sheet.mapped_fields.slice(0, 3).map((field) => (
                            <Typography key={`${sheet.sheet_name}-${field.source_header}`} variant="caption" display="block">
                              {field.source_header} → {field.target_field} ({Math.round(field.confidence * 100)}%)
                            </Typography>
                          ))}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Stack>
            ) : null}
>>>>>>> 5f0973541797732f99516ee792729f7f3cef10c2
          </Stack>
        </Paper>
      </Stack>

      <ConfirmationDialog
        open={confirmOpen}
        title="Confirmar carga da base de consulta"
        confirmLabel="Sim, executar carga"
        confirmColor="error"
        isLoading={executeMutation.isPending}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={handleExecute}
      >
        <Stack spacing={1.25}>
          <Typography variant="body2">
            Esta operação grava dados no banco e pode substituir informações homologadas.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Fonte: {sourceType} | Arquivo: {selectedFile?.name ?? 'não selecionado'}
          </Typography>
          {preview ? (
            <Typography variant="body2" color="text.secondary">
              Estimativa do preview: {preview.estimated_records} registros.
            </Typography>
          ) : null}
        </Stack>
      </ConfirmationDialog>
    </>
  );
}
