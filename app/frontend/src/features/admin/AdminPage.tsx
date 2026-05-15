import CloudUploadOutlinedIcon from '@mui/icons-material/CloudUploadOutlined';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import SmartToyOutlinedIcon from '@mui/icons-material/SmartToyOutlined';
import TableChartOutlinedIcon from '@mui/icons-material/TableChartOutlined';
import {
  Alert,
  Box,
  Button,
  Chip,
  Divider,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

import { ConfirmationDialog } from '../../shared/components/ConfirmationDialog';
import { PageHeader } from '../../shared/components/PageHeader';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { adminApi } from '../../shared/services/api/adminApi';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import { bcuApi } from '../../shared/services/api/bcuApi';

export function AdminPage() {
  const { showMessage } = useFeedback();
  const queryClient = useQueryClient();

  // ── TCPO state ────────────────────────────────────────────────────────────
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);

  // ── BCU state ─────────────────────────────────────────────────────────────
  const [bcuFile, setBcuFile] = useState<File | null>(null);
  const [proposalPattern, setProposalPattern] = useState('');

  const settingsQuery = useQuery({
    queryKey: ['admin-settings'],
    queryFn: adminApi.getSettings,
  });

  const settingsMutation = useMutation({
    mutationFn: () => adminApi.updateSettings({ proposal_number_pattern: proposalPattern || settingsQuery.data?.proposal_number_pattern || 'PROP-{YYYY}-{seq:04d}' }),
    onSuccess: (data) => {
      setProposalPattern(data.proposal_number_pattern);
      void queryClient.invalidateQueries({ queryKey: ['admin-settings'] });
      showMessage('Padrão de numeração salvo.');
    },
    onError: (error) => showMessage(extractApiErrorMessage(error, 'Erro ao salvar configuração.'), 'error'),
  });

  // ── TCPO: ETL upload + execute + auto-embeddings ──────────────────────────
  const executeMutation = useMutation({
    mutationFn: async (file: File) => {
      const upload = await adminApi.uploadTcpo(file);
      return adminApi.executeEtl({
        parse_token_tcpo: upload.parse_token,
        mode: 'upsert',
        recomputar_embeddings: true,
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
    onSuccess: () => {
      setBcuFile(null);
      void queryClient.invalidateQueries({ queryKey: ['bcu'] });
      showMessage('BCU importada com sucesso.');
    },
  });

  // ── Embeddings ────────────────────────────────────────────────────────────
  const computeEmbeddingsMutation = useMutation({
    mutationFn: () => adminApi.computeEmbeddings(),
    onSuccess: (data) => {
      showMessage(`Embeddings computados: ${data.embeddings_computados} itens processados.`);
    },
  });


  return (
    <>
      <PageHeader
        title="Administração"
        description="Configurações avançadas do sistema. Área restrita a administradores."
      />

      <Stack spacing={3}>
        <Paper sx={{ p: 3, border: '1px solid', borderColor: 'divider' }}>
          <Stack spacing={2} sx={{ maxWidth: 560 }}>
            <Typography variant="h6">Numeração de propostas</Typography>
            <Typography variant="body2" color="text.secondary">Use {'{YYYY}'}, {'{YY}'}, {'{MM}'} e {'{seq:04d}'} para gerar os próximos números.</Typography>
            <TextField label="Pattern" value={proposalPattern || settingsQuery.data?.proposal_number_pattern || ''} onChange={(event) => setProposalPattern(event.target.value)} placeholder="PROP-{YYYY}-{seq:04d}" fullWidth />
            <Button variant="contained" disabled={settingsMutation.isPending || settingsQuery.isLoading} onClick={() => settingsMutation.mutate()} sx={{ alignSelf: 'flex-start' }}>
              {settingsMutation.isPending ? 'Salvando...' : 'Salvar padrão'}
            </Button>
          </Stack>
        </Paper>
        {/* ── TCPO ─────────────────────────────────────────────────────────── */}
        <Paper
          sx={{
            p: 3,
            border: '1px solid',
            borderColor: 'divider',
            background: 'linear-gradient(145deg, rgba(20,95,185,0.06), rgba(227,181,5,0.05))',
          }}
        >
          <Stack direction={{ xs: 'column', lg: 'row' }} spacing={3} alignItems="flex-start">
            {/* ── Left: upload controls ──────────────────────────────────────── */}
            <Stack spacing={2.5} sx={{ flex: 1, minWidth: 0 }}>
              <Stack direction="row" spacing={1.5} alignItems="center">
                <CloudUploadOutlinedIcon color="primary" />
                <Typography variant="h6">Carga TCPO — Composições PINI</Typography>
              </Stack>

              <Typography variant="body2" color="text.secondary">
                Importa serviços e insumos TCPO para o catálogo de referência. Embeddings semânticos
                são disparados em segundo plano automaticamente após a carga.
              </Typography>

              <Button component="label" variant="outlined" sx={{ width: { xs: '100%', md: 340 } }}>
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

              <Button
                color="warning"
                variant="contained"
                startIcon={<CloudUploadOutlinedIcon />}
                disabled={executeMutation.isPending || !selectedFile}
                onClick={() => setConfirmOpen(true)}
                sx={{ width: { xs: '100%', md: 260 } }}
              >
                {executeMutation.isPending ? 'Executando carga...' : 'Executar carga no banco'}
              </Button>

              {executeMutation.isError && (
                <Alert severity="error">
                  {extractApiErrorMessage(executeMutation.error, 'Falha na execução da carga TCPO.')}
                </Alert>
              )}
              {executeMutation.isSuccess && (
                <Alert severity="success">
                  Carga TCPO concluída. Embeddings sendo processados em segundo plano.
                </Alert>
              )}
            </Stack>

            <Divider orientation="vertical" flexItem sx={{ display: { xs: 'none', lg: 'block' } }} />
            <Divider sx={{ display: { xs: 'block', lg: 'none' } }} />

            {/* ── Right: format documentation ───────────────────────────────── */}
            <Stack spacing={2} sx={{ flex: 1.1, minWidth: 0 }}>
              <Stack direction="row" spacing={1} alignItems="center">
                <InfoOutlinedIcon fontSize="small" color="primary" />
                <Typography variant="subtitle2" fontWeight={700}>Formato da planilha TCPO</Typography>
              </Stack>

              <Stack spacing={0.5}>
                <Typography variant="body2"><strong>Arquivo:</strong> <code>Composições TCPO - PINI.xlsx</code></Typography>
                <Typography variant="body2"><strong>2 abas obrigatórias:</strong></Typography>
              </Stack>

              <Box sx={{ overflowX: 'auto' }}>
                <Table size="small" sx={{ mb: 1.5 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700, fontSize: '0.72rem', py: 0.75, bgcolor: 'action.hover' }}>Aba</TableCell>
                      <TableCell sx={{ fontWeight: 700, fontSize: '0.72rem', py: 0.75, bgcolor: 'action.hover' }}>Colunas</TableCell>
                      <TableCell sx={{ fontWeight: 700, fontSize: '0.72rem', py: 0.75, bgcolor: 'action.hover' }}>Uso</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow>
                      <TableCell sx={{ fontSize: '0.8rem', py: 0.5 }}><code>Composições sintéticas</code></TableCell>
                      <TableCell sx={{ fontSize: '0.8rem', py: 0.5 }}>CÓDIGO · DESCRIÇÃO · UNIDADE · PREÇO</TableCell>
                      <TableCell sx={{ fontSize: '0.8rem', py: 0.5 }}>Resumo de todos os serviços (seed)</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell sx={{ fontSize: '0.8rem', py: 0.5 }}><code>Composições analíticas</code></TableCell>
                      <TableCell sx={{ fontSize: '0.8rem', py: 0.5 }}>CÓDIGO · DESCRIÇÃO · CLASS · UNIDADE · COEF. · PREÇO(R$) · TOTAL</TableCell>
                      <TableCell sx={{ fontSize: '0.8rem', py: 0.5 }}>BOM completo (pai → filho)</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </Box>

              <Stack spacing={0.5}>
                <Typography variant="body2"><strong>CLASS</strong> na aba analíticas:</Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  <Chip label="SER.CG = Serviço pai" size="small" color="primary" variant="outlined" />
                  <Chip label="MAT. = Material" size="small" color="default" variant="outlined" />
                  <Chip label="M.O. = Mão de obra" size="small" color="default" variant="outlined" />
                  <Chip label="EQP. = Equipamento" size="small" color="default" variant="outlined" />
                  <Chip label="FER. = Ferramenta" size="small" color="default" variant="outlined" />
                </Stack>
              </Stack>

              <Alert severity="info" icon={false} sx={{ py: 0.75 }}>
                <Typography variant="body2">
                  <strong>Serviços-pai</strong> têm descrição em <strong>negrito</strong> e recuo
                  zero na aba analíticas. Os insumos-filho imediatamente abaixo são vinculados ao
                  pai mais recente. Não altere a estrutura de colunas nem remova cabeçalhos.
                </Typography>
              </Alert>
            </Stack>
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

        {/* ── BCU ───────────────────────────────────────────────────────────── */}
        <Paper
          sx={{
            p: 3,
            border: '1px solid',
            borderColor: 'divider',
            background: 'linear-gradient(145deg, rgba(20,130,60,0.06), rgba(20,130,60,0.03))',
          }}
        >
          <Stack direction={{ xs: 'column', lg: 'row' }} spacing={3} alignItems="flex-start">
            {/* ── Left: upload ──────────────────────────────────────────────── */}
            <Stack spacing={2.5} sx={{ flex: 1, minWidth: 0 }}>
              <Stack direction="row" spacing={1.5} alignItems="center">
                <TableChartOutlinedIcon color="success" />
                <Typography variant="h6">Carga BCU — Base de Custos Unitários</Typography>
              </Stack>

              <Typography variant="body2" color="text.secondary">
                Importa os custos de mão de obra, equipamentos, ferramentas, EPI e exames para a
                base BCU utilizada na composição de preços.
              </Typography>

              <Button
                component="label"
                variant="outlined"
                color="success"
                sx={{ width: { xs: '100%', md: 340 } }}
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
                sx={{ width: { xs: '100%', md: 260 } }}
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

            <Divider orientation="vertical" flexItem sx={{ display: { xs: 'none', lg: 'block' } }} />
            <Divider sx={{ display: { xs: 'block', lg: 'none' } }} />

            {/* ── Right: format docs ────────────────────────────────────────── */}
            <Stack spacing={2} sx={{ flex: 1.1, minWidth: 0 }}>
              <Stack direction="row" spacing={1} alignItems="center">
                <InfoOutlinedIcon fontSize="small" color="success" />
                <Typography variant="subtitle2" fontWeight={700}>Formato da planilha BCU</Typography>
              </Stack>

              <Stack spacing={0.5}>
                <Typography variant="body2"><strong>Arquivo:</strong> <code>Converter em Data Center.xlsx</code></Typography>
                <Typography variant="body2"><strong>6 abas obrigatórias:</strong></Typography>
              </Stack>

              <Box sx={{ overflowX: 'auto' }}>
                <Table size="small" sx={{ mb: 1 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700, fontSize: '0.72rem', py: 0.75, bgcolor: 'action.hover' }}>Aba</TableCell>
                      <TableCell sx={{ fontWeight: 700, fontSize: '0.72rem', py: 0.75, bgcolor: 'action.hover' }}>Conteúdo</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {[
                      ['MÃO DE OBRA', 'Funções, salários, encargos, benefícios, custo/hora'],
                      ['EQUIPAMENTOS', 'Equipamentos com custo de aluguel R$/h e premissas'],
                      ['ENCARGOS', 'Percentuais de encargos sociais por categoria'],
                      ['EPI-UNIFORME', 'EPIs e uniformes com código, descrição, unidade, preço'],
                      ['FERRAMENTAS', 'Ferramentas com código, unidade, quantidade, preço'],
                      ['EXAMES', 'Exames médicos com código, descrição, preço unitário'],
                    ].map(([aba, desc]) => (
                      <TableRow key={aba}>
                        <TableCell sx={{ fontSize: '0.8rem', py: 0.5 }}><code>{aba}</code></TableCell>
                        <TableCell sx={{ fontSize: '0.8rem', py: 0.5 }}>{desc}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Box>

              <Alert severity="info" icon={false} sx={{ py: 0.75 }}>
                <Typography variant="body2">
                  A 1ª linha de cada aba é o cabeçalho e é ignorada. Não altere os nomes das abas.
                  Dados ausentes são gravados como <code>—</code> e podem ser preenchidos
                  posteriormente via nova importação.
                </Typography>
              </Alert>
            </Stack>
          </Stack>
        </Paper>

        {/* ── Embeddings ─────────────────────────────────────────────────────── */}
        <Paper
          sx={{
            p: 3,
            border: '1px solid',
            borderColor: 'divider',
            background: 'linear-gradient(145deg, rgba(100,60,180,0.06), rgba(100,60,180,0.02))',
          }}
        >
          <Stack spacing={2.5}>
            <Stack direction="row" spacing={1.5} alignItems="center">
              <SmartToyOutlinedIcon color="secondary" />
              <Typography variant="h6">Embeddings semânticos</Typography>
            </Stack>

            <Typography variant="body2" color="text.secondary">
              Computa vetores de embedding para todos os itens TCPO que ainda não possuírem vetor. Use este
              botão após uma carga TCPO se a busca inteligente não estiver retornando resultados esperados.
            </Typography>

            <Button
              variant="outlined"
              color="secondary"
              startIcon={<SmartToyOutlinedIcon />}
              disabled={computeEmbeddingsMutation.isPending}
              sx={{ width: { xs: '100%', md: 280 } }}
              onClick={() => computeEmbeddingsMutation.mutate()}
            >
              {computeEmbeddingsMutation.isPending ? 'Processando embeddings...' : 'Computar embeddings ausentes'}
            </Button>

            {computeEmbeddingsMutation.isError && (
              <Alert severity="error">
                {extractApiErrorMessage(computeEmbeddingsMutation.error, 'Falha ao computar embeddings.')}
              </Alert>
            )}

            {computeEmbeddingsMutation.isSuccess && (
              <Alert severity="success">
                Embeddings computados com sucesso.
              </Alert>
            )}
          </Stack>
        </Paper>
      </Stack>
    </>
  );
}

