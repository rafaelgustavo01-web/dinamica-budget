import CloudUploadOutlinedIcon from '@mui/icons-material/CloudUploadOutlined';
import {
  Alert,
  Box,
  Button,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import { useMutation } from '@tanstack/react-query';
import { useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { useAuth } from '../auth/AuthProvider';
import { PageHeader } from '../../shared/components/PageHeader';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import { smartImportApi } from '../../shared/services/api/smartImportApi';

export function SmartImportUploadPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const fileRef = useRef<HTMLInputElement>(null);
  const { selectedClientId, availableClients } = useAuth();

  const [file, setFile] = useState<File | null>(null);
  const clienteId = searchParams.get('clienteId') ?? selectedClientId;
  const clienteNome = availableClients.find((client) => client.id === clienteId)?.nome;
  const propostaId = searchParams.get('propostaId') ?? '';

  const uploadMutation = useMutation({
    mutationFn: () =>
      smartImportApi.upload({
        file: file!,
        cliente_id: clienteId.trim(),
        proposta_id: propostaId.trim() || undefined,
      }),
    onSuccess: (job) => {
      navigate(`/smart-import/${job.id}`);
    },
  });

  const canSubmit = !!file && clienteId.trim().length > 0 && !uploadMutation.isPending;

  return (
    <>
      <PageHeader
        title="Smart Import"
        description="Carregue uma planilha para importação inteligente"
      />

      <Paper sx={{ p: 3, maxWidth: 560 }}>
        <Stack spacing={3}>
          <Alert severity={clienteId ? 'info' : 'warning'}>
            {clienteId
              ? 'Cliente selecionado: ' + (clienteNome || 'cliente atual')
              : 'Selecione um cliente no topo da tela antes de importar a planilha.'}
          </Alert>

          <Box>
            <input
              ref={fileRef}
              type="file"
              accept=".xlsx,.csv"
              style={{ display: 'none' }}
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            <Stack direction="row" spacing={2} alignItems="center">
              <Button
                variant="outlined"
                startIcon={<CloudUploadOutlinedIcon />}
                onClick={() => fileRef.current?.click()}
              >
                Selecionar Arquivo
              </Button>
              {file && (
                <Typography variant="body2" color="text.secondary">
                  {file.name} ({(file.size / 1024).toFixed(0)} KB)
                </Typography>
              )}
            </Stack>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
              Formatos aceitos: .xlsx, .csv (máx. 10 MB)
            </Typography>
          </Box>

          {uploadMutation.isError && (
            <Alert severity="error">
              {extractApiErrorMessage(uploadMutation.error)}
            </Alert>
          )}

          <Button
            variant="contained"
            disabled={!canSubmit}
            onClick={() => uploadMutation.mutate()}
            loading={uploadMutation.isPending}
          >
            Importar Planilha
          </Button>
        </Stack>
      </Paper>
    </>
  );
}
