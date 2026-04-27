import BuildCircleOutlinedIcon from '@mui/icons-material/BuildCircleOutlined';
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
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useMutation } from '@tanstack/react-query';
import { useMemo, useState } from 'react';

import { ConfirmationDialog } from '../../shared/components/ConfirmationDialog';
import {
  errorMessages,
  successMessages,
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

  const embeddingsMutation = useMutation({
    mutationFn: () => adminApi.computeEmbeddings(),
    onSuccess: () => {
      showMessage(successMessages.embeddingsProcessed);
    },
  });

  const previewMutation = useMutation({
    mutationFn: (params: { file: File; sourceType: ImportSourceType }) =>
      adminApi.previewImport(params.file, params.sourceType),
    onSuccess: (data) => {
      setPreview(data);
      showMessage('Preview gerado com sucesso. Revise os mapeamentos antes de confirmar a carga.');
    },
  });

  const executeMutation = useMutation({
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

  return (
    <>
      <PageHeader
        title="Administração"
        description="Configurações avançadas do sistema. Área restrita a administradores."
      />

      <Stack spacing={3}>
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
