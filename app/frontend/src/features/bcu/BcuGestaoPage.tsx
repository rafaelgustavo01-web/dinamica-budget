import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import CloudUploadOutlinedIcon from '@mui/icons-material/CloudUploadOutlined';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import LaunchOutlinedIcon from '@mui/icons-material/LaunchOutlined';
import TableChartOutlinedIcon from '@mui/icons-material/TableChartOutlined';
import {
  Alert,
  Box,
  Button,
  Chip,
  Divider,
  Paper,
  Skeleton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ConfirmationDialog } from '../../shared/components/ConfirmationDialog';
import { HelpTooltip } from '../../shared/components/HelpTooltip';
import { PageHeader } from '../../shared/components/PageHeader';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import type { BcuCabecalho } from '../../shared/services/api/bcuApi';
import { bcuApi } from '../../shared/services/api/bcuApi';

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtDate(value: string | null | undefined): string {
  if (!value) return '—';
  try {
    return new Date(value).toLocaleDateString('pt-BR');
  } catch {
    return value;
  }
}

function fmtBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ── Styles ────────────────────────────────────────────────────────────────────

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

// ── Component ─────────────────────────────────────────────────────────────────

export function BcuGestaoPage() {
  const { showMessage } = useFeedback();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [uploadConfirmOpen, setUploadConfirmOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<BcuCabecalho | null>(null);
  const [activateTarget, setActivateTarget] = useState<BcuCabecalho | null>(null);

  const { data: cabecalhos, isLoading, error } = useQuery({
    queryKey: ['bcu-cabecalhos'],
    queryFn: () => bcuApi.listCabecalhos(),
  });

  const importMutation = useMutation({
    mutationFn: (file: File) => bcuApi.importarPlanilha(file),
    onSuccess: (data) => {
      setUploadConfirmOpen(false);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      void queryClient.invalidateQueries({ queryKey: ['bcu-cabecalhos'] });
      void queryClient.invalidateQueries({ queryKey: ['bcu-cabecalho-ativo'] });
      const msg = data.observacao
        ? `"${data.nome_arquivo}" importada. Aviso: ${data.observacao.slice(0, 120)}`
        : `"${data.nome_arquivo}" importada com sucesso. Ative-a para usar nos cálculos.`;
      showMessage(msg);
    },
    onError: (err) => {
      setUploadConfirmOpen(false);
      showMessage(extractApiErrorMessage(err, 'Erro ao importar BCU.'), 'error');
    },
  });

  const ativarMutation = useMutation({
    mutationFn: (id: string) => bcuApi.ativarCabecalho(id),
    onSuccess: (data) => {
      setActivateTarget(null);
      void queryClient.invalidateQueries({ queryKey: ['bcu-cabecalhos'] });
      void queryClient.invalidateQueries({ queryKey: ['bcu-cabecalho-ativo'] });
      showMessage(`"${data.nome_arquivo}" ativada como base principal.`);
    },
    onError: (err) => {
      setActivateTarget(null);
      showMessage(extractApiErrorMessage(err, 'Erro ao ativar BCU.'), 'error');
    },
  });

  const deletarMutation = useMutation({
    mutationFn: (id: string) => bcuApi.deletarCabecalho(id),
    onSuccess: () => {
      setDeleteTarget(null);
      void queryClient.invalidateQueries({ queryKey: ['bcu-cabecalhos'] });
      void queryClient.invalidateQueries({ queryKey: ['bcu-cabecalho-ativo'] });
      showMessage('Versão removida.');
    },
    onError: (err) => {
      setDeleteTarget(null);
      showMessage(extractApiErrorMessage(err, 'Erro ao remover versão.'), 'error');
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    setFileError(null);
    if (!file) {
      setSelectedFile(null);
      return;
    }
    if (!file.name.toLowerCase().endsWith('.xlsx')) {
      setFileError('Apenas arquivos .xlsx são aceitos.');
      setSelectedFile(null);
      e.target.value = '';
      return;
    }
    setSelectedFile(file);
  };

  const clearFile = () => {
    setSelectedFile(null);
    setFileError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <Box>
      <PageHeader
        title="Gestão da BCU"
        description="Importe, ative e gerencie versões da Base de Custos Unitários."
      />

      {/* ── Upload section ──────────────────────────────────────────────── */}
      <Paper
        variant="outlined"
        sx={{
          p: 3,
          mb: 3,
          background: 'linear-gradient(145deg, rgba(20,95,185,0.05), rgba(20,95,185,0.02))',
        }}
      >
        <Stack spacing={2}>
          <Stack direction="row" spacing={1.5} alignItems="center">
            <CloudUploadOutlinedIcon color="primary" />
            <Typography variant="h6" fontWeight={600}>
              Importar nova versão
            </Typography>
            <HelpTooltip title="Aceita a planilha 'Converter em Data Center.xlsx' com 6 abas: Mão de Obra, Equipamentos, Encargos, EPI/Uniforme, Ferramentas, Exames. A versão importada fica inativa até ser ativada." />
          </Stack>

          <Typography variant="body2" color="text.secondary">
            Selecione a planilha <strong>Converter em Data Center.xlsx</strong>. A versão será
            importada como <em>inativa</em> — ative-a manualmente após verificar os dados.
          </Typography>

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems={{ sm: 'center' }}>
            <Button
              component="label"
              variant="outlined"
              startIcon={<TableChartOutlinedIcon />}
              sx={{ minWidth: 280 }}
            >
              {selectedFile ? selectedFile.name : 'Selecionar planilha…'}
              <input
                ref={fileInputRef}
                hidden
                type="file"
                accept=".xlsx"
                onChange={handleFileChange}
              />
            </Button>

            {selectedFile && (
              <Typography variant="caption" color="text.secondary">
                {fmtBytes(selectedFile.size)}
              </Typography>
            )}

            <Button
              variant="contained"
              startIcon={<CloudUploadOutlinedIcon />}
              disabled={!selectedFile || importMutation.isPending}
              onClick={() => setUploadConfirmOpen(true)}
            >
              Importar
            </Button>

            {selectedFile && (
              <Button size="small" color="inherit" onClick={clearFile}>
                Limpar
              </Button>
            )}
          </Stack>

          {fileError && <Alert severity="warning" sx={{ py: 0.5 }}>{fileError}</Alert>}

          {importMutation.isError && (
            <Alert severity="error">
              {extractApiErrorMessage(importMutation.error, 'Falha ao importar BCU.')}
            </Alert>
          )}
        </Stack>
      </Paper>

      {/* ── Versions table ──────────────────────────────────────────────── */}
      <Stack direction="row" spacing={1} alignItems="center" mb={1.5}>
        <Typography variant="subtitle1" fontWeight={600}>
          Versões importadas
        </Typography>
        <HelpTooltip title="Apenas a versão ativa é usada nos cálculos de composição. As demais ficam arquivadas e podem ser ativadas ou removidas." />
      </Stack>

      {isLoading && (
        <Stack spacing={1}>
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} variant="rectangular" height={52} sx={{ borderRadius: 1 }} />
          ))}
        </Stack>
      )}

      {error && <Alert severity="error">Erro ao carregar versões da BCU.</Alert>}

      {!isLoading && !error && (
        <Paper variant="outlined">
          <TableContainer>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell sx={headCell}>Arquivo</TableCell>
                  <TableCell sx={headCell}>Ref.</TableCell>
                  <TableCell sx={headCell}>Importado em</TableCell>
                  <TableCell sx={headCell}>Status</TableCell>
                  <TableCell sx={{ ...headCell, textAlign: 'right' }}>Ações</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(!cabecalhos || cabecalhos.length === 0) && (
                  <TableRow>
                    <TableCell
                      colSpan={5}
                      sx={{ ...dataCell, textAlign: 'center', py: 5, color: 'text.secondary' }}
                    >
                      Nenhuma BCU importada ainda. Use o formulário acima para começar.
                    </TableCell>
                  </TableRow>
                )}

                {cabecalhos?.map((cab) => (
                  <TableRow key={cab.id} hover>
                    <TableCell sx={dataCell}>
                      <Typography
                        variant="body2"
                        fontWeight={cab.is_ativo ? 600 : 400}
                        sx={{ lineHeight: 1.3 }}
                      >
                        {cab.nome_arquivo}
                      </Typography>
                      {cab.observacao && (
                        <Tooltip title={cab.observacao} placement="top">
                          <Typography
                            variant="caption"
                            color="warning.main"
                            display="block"
                            sx={{ cursor: 'default', maxWidth: 320 }}
                          >
                            {cab.observacao.length > 70
                              ? cab.observacao.slice(0, 70) + '…'
                              : cab.observacao}
                          </Typography>
                        </Tooltip>
                      )}
                    </TableCell>

                    <TableCell sx={dataCell}>{fmtDate(cab.data_referencia)}</TableCell>
                    <TableCell sx={dataCell}>{fmtDate(cab.criado_em)}</TableCell>

                    <TableCell sx={dataCell}>
                      <Chip
                        label={cab.is_ativo ? 'Base ativa' : 'Inativa'}
                        size="small"
                        color={cab.is_ativo ? 'success' : 'default'}
                        variant={cab.is_ativo ? 'filled' : 'outlined'}
                      />
                    </TableCell>

                    <TableCell sx={{ ...dataCell, textAlign: 'right' }}>
                      <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                        {cab.is_ativo ? (
                          <Button
                            variant="outlined"
                            size="small"
                            startIcon={<LaunchOutlinedIcon />}
                            onClick={() => navigate('/bcu')}
                          >
                            Ver dados
                          </Button>
                        ) : (
                          <>
                            <Button
                              variant="outlined"
                              size="small"
                              startIcon={<CheckCircleOutlineIcon />}
                              onClick={() => setActivateTarget(cab)}
                              disabled={ativarMutation.isPending}
                            >
                              Ativar
                            </Button>
                            <Button
                              variant="outlined"
                              size="small"
                              color="error"
                              startIcon={<DeleteOutlineIcon />}
                              onClick={() => setDeleteTarget(cab)}
                              disabled={deletarMutation.isPending}
                            >
                              Remover
                            </Button>
                          </>
                        )}
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* ── Upload confirmation ──────────────────────────────────────────── */}
      <ConfirmationDialog
        open={uploadConfirmOpen}
        title="Confirmar importação"
        confirmLabel={importMutation.isPending ? 'Importando…' : 'Importar'}
        confirmColor="primary"
        isLoading={importMutation.isPending}
        onCancel={() => !importMutation.isPending && setUploadConfirmOpen(false)}
        onConfirm={() => selectedFile && importMutation.mutate(selectedFile)}
      >
        <Stack spacing={1.5}>
          <Typography variant="body2">
            A planilha será importada como uma <strong>nova versão inativa</strong>. Você poderá
            ativá-la manualmente após verificar os dados.
          </Typography>
          <Divider />
          <Stack spacing={0.5}>
            <Typography variant="caption" color="text.secondary">
              Arquivo selecionado
            </Typography>
            <Typography variant="body2" fontWeight={600}>
              {selectedFile?.name}
            </Typography>
            {selectedFile && (
              <Typography variant="caption" color="text.secondary">
                {fmtBytes(selectedFile.size)}
              </Typography>
            )}
          </Stack>
        </Stack>
      </ConfirmationDialog>

      {/* ── Activate confirmation ────────────────────────────────────────── */}
      <ConfirmationDialog
        open={!!activateTarget}
        title="Ativar versão da BCU"
        confirmLabel={ativarMutation.isPending ? 'Ativando…' : 'Ativar'}
        confirmColor="primary"
        isLoading={ativarMutation.isPending}
        onCancel={() => !ativarMutation.isPending && setActivateTarget(null)}
        onConfirm={() => activateTarget && ativarMutation.mutate(activateTarget.id)}
      >
        <Stack spacing={1.5}>
          <Typography variant="body2">
            <strong>{activateTarget?.nome_arquivo}</strong> passará a ser a base principal de
            custos. A versão atualmente ativa será desativada.
          </Typography>
          <Alert severity="info" sx={{ py: 0.5 }}>
            A troca tem efeito imediato para todos os usuários do sistema.
          </Alert>
        </Stack>
      </ConfirmationDialog>

      {/* ── Delete confirmation ──────────────────────────────────────────── */}
      <ConfirmationDialog
        open={!!deleteTarget}
        title="Remover versão da BCU"
        confirmLabel={deletarMutation.isPending ? 'Removendo…' : 'Remover'}
        confirmColor="error"
        isLoading={deletarMutation.isPending}
        onCancel={() => !deletarMutation.isPending && setDeleteTarget(null)}
        onConfirm={() => deleteTarget && deletarMutation.mutate(deleteTarget.id)}
      >
        <Stack spacing={1.5}>
          <Typography variant="body2">
            Remover <strong>{deleteTarget?.nome_arquivo}</strong>? Todos os dados desta versão
            (mão de obra, equipamentos, encargos, EPI, ferramentas e mobilização) serão excluídos
            permanentemente.
          </Typography>
          <Alert severity="warning" sx={{ py: 0.5 }}>
            Esta ação não pode ser desfeita.
          </Alert>
        </Stack>
      </ConfirmationDialog>
    </Box>
  );
}
