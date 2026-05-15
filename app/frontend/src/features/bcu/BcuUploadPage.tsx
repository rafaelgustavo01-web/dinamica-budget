import CloudUploadOutlinedIcon from '@mui/icons-material/CloudUploadOutlined';
import TableChartOutlinedIcon from '@mui/icons-material/TableChartOutlined';
import {
  Alert,
  Box,
  Button,
  Chip,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import * as XLSX from 'xlsx';

import { PageHeader } from '../../shared/components/PageHeader';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import { bcuApi } from '../../shared/services/api/bcuApi';
import { bcuItemApi, type BcuTableType, type BcuUploadError } from '../../shared/services/api/bcuItemApi';

const TABLE_OPTIONS: { value: BcuTableType; label: string }[] = [
  { value: 'MO', label: 'Mão de Obra' },
  { value: 'EQP', label: 'Equipamentos' },
  { value: 'ENC', label: 'Encargos' },
  { value: 'EXM', label: 'Exames' },
  { value: 'EPI', label: 'EPI / Uniforme' },
  { value: 'FER', label: 'Ferramentas' },
  { value: 'MOB', label: 'Mobilização' },
];

const REQUIRED_COLS: Record<BcuTableType, string[]> = {
  MO: ['descricao_funcao'],
  EQP: ['equipamento'],
  ENC: ['tipo_encargo', 'discriminacao_encargo'],
  EXM: ['exame'],
  EPI: ['epi'],
  FER: ['descricao'],
  MOB: ['descricao'],
};

export function BcuUploadPage() {
  const { showMessage } = useFeedback();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [tabela, setTabela] = useState<BcuTableType>('MO');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewRows, setPreviewRows] = useState<Record<string, unknown>[]>([]);
  const [validationErrors, setValidationErrors] = useState<BcuUploadError[]>([]);
  const [modo, setModo] = useState<'upsert' | 'append'>('upsert');

  useEffect(() => {
    if (previewRows.length === 0) return;
    const required = REQUIRED_COLS[tabela];
    const errors: BcuUploadError[] = [];
    previewRows.forEach((row, idx) => {
      required.forEach((col) => {
        const val = row[col];
        if (val === null || val === undefined || String(val).trim() === '') {
          errors.push({ linha: idx + 2, campo: col, valor: val === null ? null : String(val), mensagem: 'Campo obrigatório ausente.' });
        }
      });
    });
    setValidationErrors(errors);
  }, [tabela, previewRows]);

  const { data: cabecalhos } = useQuery({
    queryKey: ['bcu-cabecalhos'],
    queryFn: () => bcuApi.listCabecalhos(),
  });

  const [cabecalhoId, setCabecalhoId] = useState<string>('');

  const uploadMutation = useMutation({
    mutationFn: (file: File) =>
      bcuItemApi.uploadIndividual({
        file,
        cabecalho_id: cabecalhoId,
        tabela,
        modo,
      }),
    onSuccess: (data) => {
      setSelectedFile(null);
      setPreviewRows([]);
      setValidationErrors([]);
      if (fileInputRef.current) fileInputRef.current.value = '';
      if (data.erros.length > 0) {
        showMessage(`Importado com ${data.erros.length} avisos. Verifique o preview.`, 'warning');
      } else {
        showMessage(`Upload individual concluído: ${data.linhas_inseridas} inseridas, ${data.linhas_atualizadas} atualizadas.`);
      }
    },
    onError: (err) => {
      const msg = extractApiErrorMessage(err, 'Falha no upload individual.');
      if (msg.includes('404') || msg.includes('Not Found')) {
        showMessage(
          'Endpoint de upload individual ainda não implementado no backend. Contratos TS estão prontos em bcuItemApi.ts.',
          'error',
        );
      } else {
        showMessage(msg, 'error');
      }
    },
  });

  const parsePreview = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const data = new Uint8Array(e.target?.result as ArrayBuffer);
      const workbook = XLSX.read(data, { type: 'array' });
      const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
      const json = XLSX.utils.sheet_to_json<unknown[]>(firstSheet, { header: 1, defval: null });

      // detect header row (first non-empty row)
      let headerRowIdx = 0;
      for (let i = 0; i < Math.min(json.length, 10); i++) {
        const row = json[i];
        if (row && Array.isArray(row) && row.some((c) => c !== null && c !== undefined)) {
          headerRowIdx = i;
          break;
        }
      }

      const headers = (json[headerRowIdx] ?? []).map((h: unknown) => String(h ?? '').trim().toLowerCase().replace(/\s+/g, '_'));
      const rows = json.slice(headerRowIdx + 1).map((r: unknown) => {
        const rowArray = Array.isArray(r) ? r : [];
        const obj: Record<string, unknown> = {};
        rowArray.forEach((cell, idx) => {
          obj[headers[idx] ?? `col_${idx}`] = cell;
        });
        return obj;
      }).filter((r: Record<string, unknown>) => Object.values(r).some((v) => v !== null && v !== undefined));

      setPreviewRows(rows.slice(0, 20));

      // validate
      const errors: BcuUploadError[] = [];
      const required = REQUIRED_COLS[tabela];
      rows.forEach((row: Record<string, unknown>, idx: number) => {
        required.forEach((col) => {
          const val = row[col];
          if (val === null || val === undefined || String(val).trim() === '') {
            errors.push({ linha: idx + 2, campo: col, valor: val === null ? null : String(val), mensagem: 'Campo obrigatório ausente.' });
          }
        });
      });
      setValidationErrors(errors);
    };
    reader.readAsArrayBuffer(file);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    setSelectedFile(file);
    setPreviewRows([]);
    setValidationErrors([]);
    if (file) {
      if (!file.name.toLowerCase().endsWith('.xlsx') && !file.name.toLowerCase().endsWith('.csv')) {
        showMessage('Apenas arquivos .xlsx ou .csv são aceitos.', 'error');
        setSelectedFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
        return;
      }
      parsePreview(file);
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
    setPreviewRows([]);
    setValidationErrors([]);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <Box>
      <PageHeader
        title="Upload Individual de Base"
        description="Importe uma única tabela (Mão de Obra, Equipamentos, Encargos, Exames, EPI, Ferramentas ou Mobilização) para uma versão BCU existente."
      />

      <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
        <Stack spacing={2.5}>
          <Stack direction="row" spacing={1.5} alignItems="center">
            <CloudUploadOutlinedIcon color="primary" />
            <Typography variant="h6" fontWeight={600}>
              Configurar importação
            </Typography>
          </Stack>

          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <FormControl sx={{ minWidth: 240 }}>
              <InputLabel id="tabela-label">Tabela</InputLabel>
              <Select
                labelId="tabela-label"
                value={tabela}
                label="Tabela"
                onChange={(e) => setTabela(e.target.value as BcuTableType)}
              >
                {TABLE_OPTIONS.map((opt) => (
                  <MenuItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl sx={{ minWidth: 280 }}>
              <InputLabel id="cabecalho-label">Versão BCU (cabeçalho)</InputLabel>
              <Select
                labelId="cabecalho-label"
                value={cabecalhoId}
                label="Versão BCU (cabeçalho)"
                onChange={(e) => setCabecalhoId(e.target.value)}
              >
                {cabecalhos?.map((c) => (
                  <MenuItem key={c.id} value={c.id}>
                    {c.nome_arquivo} {c.is_ativo ? '(ativa)' : ''}
                  </MenuItem>
                )) ?? (
                  <MenuItem disabled value="">
                    Nenhuma BCU importada
                  </MenuItem>
                )}
              </Select>
            </FormControl>

            <FormControl sx={{ minWidth: 160 }}>
              <InputLabel id="modo-label">Modo</InputLabel>
              <Select
                labelId="modo-label"
                value={modo}
                label="Modo"
                onChange={(e) => setModo(e.target.value as 'upsert' | 'append')}
              >
                <MenuItem value="upsert">Substituir (upsert)</MenuItem>
                <MenuItem value="append">Acrescentar</MenuItem>
              </Select>
            </FormControl>
          </Stack>

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems={{ sm: 'center' }}>
            <Button component="label" variant="outlined" sx={{ minWidth: 320 }} startIcon={<TableChartOutlinedIcon />}>
              {selectedFile ? selectedFile.name : 'Selecionar planilha…'}
              <input ref={fileInputRef} hidden type="file" accept=".xlsx,.csv" onChange={handleFileChange} />
            </Button>

            {selectedFile && (
              <Typography variant="caption" color="text.secondary">
                {(selectedFile.size / 1024).toFixed(1)} KB
              </Typography>
            )}

            <Button
              variant="contained"
              startIcon={<CloudUploadOutlinedIcon />}
              disabled={!selectedFile || !cabecalhoId || uploadMutation.isPending || validationErrors.length > 0}
              onClick={() => selectedFile && uploadMutation.mutate(selectedFile)}
            >
              {uploadMutation.isPending ? 'Enviando…' : 'Enviar para backend'}
            </Button>

            {selectedFile && (
              <Button size="small" color="inherit" onClick={clearFile}>
                Limpar
              </Button>
            )}
          </Stack>

          {validationErrors.length > 0 && (
            <Alert severity="warning">
              <Typography variant="body2" fontWeight={600}>
                {validationErrors.length} erro(s) de validação encontrados no preview:
              </Typography>
              <Box component="ul" sx={{ pl: 2, mt: 0.5, mb: 0 }}>
                {validationErrors.slice(0, 10).map((e, i) => (
                  <li key={i}>
                    <Typography variant="caption">
                      Linha {e.linha}, coluna "{e.campo}": {e.mensagem}
                    </Typography>
                  </li>
                ))}
                {validationErrors.length > 10 && (
                  <li>
                    <Typography variant="caption">…e mais {validationErrors.length - 10} erro(s).</Typography>
                  </li>
                )}
              </Box>
            </Alert>
          )}

          {uploadMutation.isError && (
            <Alert severity="error">
              {extractApiErrorMessage(uploadMutation.error, 'Falha no upload individual.')}
            </Alert>
          )}

          {uploadMutation.isSuccess && (
            <Alert severity="success">Upload processado com sucesso.</Alert>
          )}
        </Stack>
      </Paper>

      {previewRows.length > 0 && (
        <Paper variant="outlined" sx={{ p: 2 }}>
          <Stack direction="row" spacing={1} alignItems="center" mb={1.5}>
            <Typography variant="subtitle1" fontWeight={600}>
              Preview (primeiras 20 linhas)
            </Typography>
            <Chip label={tabela} size="small" color="primary" />
          </Stack>
          <TableContainer sx={{ maxHeight: 400 }}>
            <Table size="small" stickyHeader>
              <TableHead>
                <TableRow>
                  {Object.keys(previewRows[0]).map((k) => (
                    <TableCell key={k} sx={{ fontWeight: 700, fontSize: '0.72rem', textTransform: 'uppercase' }}>
                      {k}
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {previewRows.map((row, i) => (
                  <TableRow key={i}>
                    {Object.values(row).map((v, j) => (
                      <TableCell key={j} sx={{ fontSize: '0.8rem' }}>
                        {v === null || v === undefined ? '—' : String(v)}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}
    </Box>
  );
}
