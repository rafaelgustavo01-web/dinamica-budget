import CloudUploadOutlinedIcon from '@mui/icons-material/CloudUploadOutlined';
import PreviewOutlinedIcon from '@mui/icons-material/PreviewOutlined';

import TableChartOutlinedIcon from '@mui/icons-material/TableChartOutlined';
import {
  Alert,
  Box,
  Button,
  Chip,
  LinearProgress,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useMemo, useState } from 'react';

import { ConfirmationDialog } from '../../shared/components/ConfirmationDialog';
import { PageHeader } from '../../shared/components/PageHeader';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { adminApi } from '../../shared/services/api/adminApi';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import { bcuApi } from '../../shared/services/api/bcuApi';
import type { ImportPreviewResponse } from '../../shared/types/contracts/admin';

export function UploadTcpoPage() {
  const { showMessage } = useFeedback();
  const queryClient = useQueryClient();

  // ── TCPO state ────────────────────────────────────────────────────────────
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);

  // ── BCU state ─────────────────────────────────────────────────────────────
  const [bcuFile, setBcuFile] = useState<File | null>(null);

  // ── TCPO: semantic preview (display only) ────────────────────────────────
  const previewMutation = useMutation({
    mutationFn: (file: File) => adminApi.previewImport(file, 'TCPO'),
    onSuccess: (data) => {
      setPreview(data);
      showMessage('Preview TCPO gerado. Revise os mapeamentos antes de executar.');
    },
  });

  // ── TCPO: proper ETL execute (upload → execute) ──────────────────────────
  const executeMutation = useMutation({
    mutationFn: async (file: File) => {
      const upload = await adminApi.uploadTcpo(file);
      return adminApi.executeEtl({
        parse_token_tcpo: upload.parse_token,
        mode: 'upsert',
        recomputar_embeddings: false,
      });
    },
    onSuccess: (data) => {
      setConfirmOpen(false);
      showMessage(
        `Carga TCPO concluída: ${data.itens_inseridos} inseridos, ${data.itens_atualizados} atualizados, ${data.relacoes_inseridas} relações.`,
      );
    },
  });

  // ── BCU ───────────────────────────────────────────────────────────────────
  const bcuImportMutation = useMutation({
    mutationFn: (file: File) => bcuApi.importarPlanilha(file),
    onSuccess: (data) => {
      setBcuFile(null);
      void queryClient.invalidateQueries({ queryKey: ['bcu'] });
      showMessage(`BCU importada com sucesso! ID: ${data.id}`);
    },
  });

  const confidenceAvg = useMemo(() => {
    if (!preview) return 0;
    const all = preview.sheets.flatMap((sheet) => sheet.mapped_fields);
    if (!all.length) return 0;
    return all.reduce((acc, item) => acc + item.confidence, 0) / all.length;
  }, [preview]);

  return (
    <>
      <PageHeader
        title="Upload de Tabelas"
        description="Carregue as planilhas de referência: TCPO e BCU (Base de Custos Unitários)."
      />

      {/* ── TCPO ─────────────────────────────────────────────────────────── */}
      <Paper
        sx={{
          p: 3,
          border: '1px solid',
          borderColor: 'divider',
          background: 'linear-gradient(145deg, rgba(20,95,185,0.06), rgba(227,181,5,0.05))',
        }}
      >
        <Stack spacing={2.5}>
          <Stack direction="row" spacing={1.5} alignItems="center">
            <CloudUploadOutlinedIcon color="primary" />
            <Typography variant="h6">Carga da planilha TCPO (Composições PINI)</Typography>
          </Stack>

          <Typography variant="body2" color="text.secondary">
            Selecione a planilha, gere o preview semântico e execute a carga somente após validar o mapeamento.
          </Typography>

          <Button component="label" variant="outlined" sx={{ width: { xs: '100%', md: 360 } }}>
            {selectedFile ? selectedFile.name : 'Selecionar Composições TCPO - PINI.xlsx'}
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

          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
            <Button
              variant="contained"
              startIcon={<PreviewOutlinedIcon />}
              disabled={previewMutation.isPending || !selectedFile}
              onClick={() => selectedFile && previewMutation.mutate(selectedFile)}
            >
              {previewMutation.isPending ? 'Gerando preview...' : 'Gerar preview'}
            </Button>

            <Button
              color="warning"
              variant="contained"
              disabled={executeMutation.isPending || !selectedFile}
              onClick={() => setConfirmOpen(true)}
            >
              {executeMutation.isPending ? 'Executando carga...' : 'Executar carga no banco'}
            </Button>
          </Stack>

          {previewMutation.isError && (
            <Alert severity="error">
              {extractApiErrorMessage(previewMutation.error, 'Falha ao gerar preview da planilha TCPO.')}
            </Alert>
          )}

          {executeMutation.isError && (
            <Alert severity="error">
              {extractApiErrorMessage(executeMutation.error, 'Falha na execução da carga TCPO.')}
            </Alert>
          )}

          {preview && (
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

              {preview.warnings.length > 0 && (
                <Alert severity="warning">{preview.warnings.join(' | ')}</Alert>
              )}

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
                        {sheet.mapped_fields.slice(0, 4).map((field) => (
                          <Typography
                            key={`${sheet.sheet_name}-${field.source_header}`}
                            variant="caption"
                            display="block"
                          >
                            {field.source_header} → {field.target_field} ({Math.round(field.confidence * 100)}%)
                          </Typography>
                        ))}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Stack>
          )}
        </Stack>
      </Paper>

      <ConfirmationDialog
        open={confirmOpen}
        title="Confirmar carga TCPO"
        confirmLabel="Sim, executar carga"
        confirmColor="error"
        isLoading={executeMutation.isPending}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={() => selectedFile && executeMutation.mutate(selectedFile)}
      >
        <Stack spacing={1.25}>
          <Typography variant="body2">
            Esta operação grava dados no banco e pode substituir informações homologadas.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Fonte: TCPO | Arquivo: {selectedFile?.name ?? 'não selecionado'}
          </Typography>
          {preview && (
            <Typography variant="body2" color="text.secondary">
              Estimativa do preview: {preview.estimated_records} registros.
            </Typography>
          )}
        </Stack>
      </ConfirmationDialog>

      {/* ── BCU Tabelas ───────────────────────────────────────────────────── */}
      <Paper
        sx={{
          p: 3,
          border: '1px solid',
          borderColor: 'divider',
          background: 'linear-gradient(145deg, rgba(20,130,60,0.06), rgba(20,130,60,0.03))',
        }}
      >
        <Stack spacing={2.5}>
          <Stack direction="row" spacing={1.5} alignItems="center">
            <TableChartOutlinedIcon color="success" />
            <Typography variant="h6">Carga da planilha BCU (Base de Custos Unitários)</Typography>
            <Chip label="7 abas" size="small" color="success" variant="outlined" />
          </Stack>

          <Typography variant="body2" color="text.secondary">
            Importa todas as abas da planilha BCU: Mão de Obra, Equipamentos, Encargos, EPI/Uniforme,
            Ferramentas e Mobilização. Dados existentes com o mesmo nome de arquivo são substituídos.
          </Typography>

          <Button
            component="label"
            variant="outlined"
            color="success"
            sx={{ width: { xs: '100%', md: 360 } }}
          >
            {bcuFile ? bcuFile.name : 'Selecionar BCU tabelas.xlsx'}
            <input
              hidden
              type="file"
              accept=".xlsx"
              onChange={(event) => {
                const file = event.target.files?.[0] ?? null;
                setBcuFile(file);
              }}
            />
          </Button>

          <Button
            variant="contained"
            color="success"
            startIcon={<CloudUploadOutlinedIcon />}
            disabled={!bcuFile || bcuImportMutation.isPending}
            sx={{ width: { xs: '100%', md: 280 } }}
            onClick={() => bcuFile && bcuImportMutation.mutate(bcuFile)}
          >
            {bcuImportMutation.isPending ? 'Importando...' : 'Importar BCU'}
          </Button>

          {bcuImportMutation.isError && (
            <Alert severity="error">
              {extractApiErrorMessage(bcuImportMutation.error, 'Falha ao importar BCU.')}
            </Alert>
          )}

          {bcuImportMutation.isSuccess && (
            <Alert severity="success">BCU importada com sucesso!</Alert>
          )}
        </Stack>
      </Paper>
    </>
  );
}
