import CloudUploadOutlinedIcon from '@mui/icons-material/CloudUploadOutlined';

import TableChartOutlinedIcon from '@mui/icons-material/TableChartOutlined';
import {
  Alert,
  Button,
  Chip,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { ConfirmationDialog } from '../../shared/components/ConfirmationDialog';
import { PageHeader } from '../../shared/components/PageHeader';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { adminApi } from '../../shared/services/api/adminApi';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import { bcuApi } from '../../shared/services/api/bcuApi';

export function UploadTcpoPage() {
  const { showMessage } = useFeedback();
  const queryClient = useQueryClient();

  // ── TCPO state ────────────────────────────────────────────────────────────
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);

  // ── BCU state ─────────────────────────────────────────────────────────────
  const [bcuFile, setBcuFile] = useState<File | null>(null);

  // ── TCPO: ETL upload + execute (single-shot) ─────────────────────────────
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
            Selecione a planilha "Composições TCPO - PINI.xlsx" e execute a carga. O parser identifica
            serviços-pai por bold + indent + prefixo SER. e popula referencia.base_tcpo + composicao_base.
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
              }}
            />
          </Button>

          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1}>
            <Button
              color="warning"
              variant="contained"
              startIcon={<CloudUploadOutlinedIcon />}
              disabled={executeMutation.isPending || !selectedFile}
              onClick={() => setConfirmOpen(true)}
            >
              {executeMutation.isPending ? 'Executando carga...' : 'Executar carga no banco'}
            </Button>
          </Stack>

          {executeMutation.isError && (
            <Alert severity="error">
              {extractApiErrorMessage(executeMutation.error, 'Falha na execução da carga TCPO.')}
            </Alert>
          )}

          {executeMutation.isSuccess && (
            <Alert severity="success">Carga TCPO concluída com sucesso.</Alert>
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
            <Chip label="6 abas" size="small" color="success" variant="outlined" />
          </Stack>

          <Typography variant="body2" color="text.secondary">
            Fonte oficial: <strong>Converter em Data Center.xlsx</strong> — 6 abas:
            Mão de Obra, Equipamentos, Encargos, EPI/Uniforme, Ferramentas, Exames.
            Dados existentes com o mesmo nome de arquivo são substituídos. EXAMES é registrado
            como aviso (sem tabela-alvo no schema atual).
          </Typography>

          <Button
            component="label"
            variant="outlined"
            color="success"
            sx={{ width: { xs: '100%', md: 360 } }}
          >
            {bcuFile ? bcuFile.name : 'Selecionar Converter em Data Center.xlsx'}
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
