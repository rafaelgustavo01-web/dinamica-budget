import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Paper, Stack, Typography, Button, Alert, Box, CircularProgress, LinearProgress } from '@mui/material';
import CloudUploadOutlinedIcon from '@mui/icons-material/CloudUploadOutlined';
import AutoFixHighOutlinedIcon from '@mui/icons-material/AutoFixHighOutlined';
import ArrowBackOutlinedIcon from '@mui/icons-material/ArrowBackOutlined';

import { PageHeader } from '../../../shared/components/PageHeader';
import { proposalsApi } from '../../../shared/services/api/proposalsApi';
import { extractApiErrorMessage } from '../../../shared/services/api/apiClient';

export function ProposalImportPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);

  const { data: proposta, isLoading: loadingProposta, isError: isErrorProposta, error: errorProposta } = useQuery({
    queryKey: ['proposta', id],
    queryFn: () => proposalsApi.getById(id!),
    enabled: Boolean(id),
  });

  const uploadMutation = useMutation({
    mutationFn: (f: File) => proposalsApi.uploadPq(id!, f),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['proposta', id] });
      setFile(null);
    },
  });

  const matchMutation = useMutation({
    mutationFn: () => proposalsApi.executeMatch(id!),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['proposta', id] });
    },
  });

  if (loadingProposta) return (
    <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
      <CircularProgress />
    </Box>
  );

  if (isErrorProposta || !proposta) {
    return (
      <>
        <PageHeader
          title="Importar Planilha (PQ)"
          description="Erro ao carregar proposta"
          actions={
            <Button
              variant="outlined"
              startIcon={<ArrowBackOutlinedIcon />}
              onClick={() => navigate('/propostas')}
            >
              Voltar
            </Button>
          }
        />
        <Alert severity="error">
          {extractApiErrorMessage(errorProposta, 'Não foi possível carregar a proposta. Verifique a URL e tente novamente.')}
        </Alert>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Importar Planilha (PQ)"
        description={`Proposta ${proposta?.codigo || ''}`}
        actions={
          <Button
            variant="outlined"
            startIcon={<ArrowBackOutlinedIcon />}
            onClick={() => navigate(`/propostas/${id}`)}
          >
            Voltar
          </Button>
        }
      />

      <Stack spacing={3}>
        {uploadMutation.isError ? (
          <Alert severity="error">{extractApiErrorMessage(uploadMutation.error)}</Alert>
        ) : null}
        {matchMutation.isError ? (
          <Alert severity="error">{extractApiErrorMessage(matchMutation.error)}</Alert>
        ) : null}

        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>1. Carregar Arquivo</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Selecione uma planilha Excel (.xlsx) ou CSV contendo a lista de serviços e quantidades.
          </Typography>

          <Box
            sx={{
              border: '2px dashed',
              borderColor: 'divider',
              borderRadius: 1,
              p: 4,
              textAlign: 'center',
              bgcolor: 'action.hover',
              mb: 2,
            }}
          >
            <input
              type="file"
              accept=".xlsx,.csv"
              id="pq-file-upload"
              style={{ display: 'none' }}
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            <label htmlFor="pq-file-upload">
              <Button
                variant="outlined"
                component="span"
                startIcon={<CloudUploadOutlinedIcon />}
              >
                {file ? 'Trocar Arquivo' : 'Selecionar Arquivo'}
              </Button>
            </label>
            {file && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                Selecionado: <strong>{file.name}</strong>
              </Typography>
            )}
          </Box>

          <Button
            variant="contained"
            disabled={!file || uploadMutation.isPending}
            onClick={() => file && uploadMutation.mutate(file)}
          >
            {uploadMutation.isPending ? 'Enviando...' : 'Enviar Planilha'}
          </Button>

          {uploadMutation.isSuccess && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Planilha importada com sucesso: {uploadMutation.data.linhas_importadas} linhas processadas.
            </Alert>
          )}
        </Paper>

        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>2. Match Inteligente</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Associe os itens da planilha importada ao catálogo TCPO e itens próprios automaticamente.
          </Typography>

          <Button
            variant="contained"
            color="secondary"
            startIcon={<AutoFixHighOutlinedIcon />}
            disabled={proposta.status === 'RASCUNHO' || matchMutation.isPending || uploadMutation.isPending}
            onClick={() => matchMutation.mutate()}
          >
            {matchMutation.isPending ? 'Processando Match...' : 'Executar Match Inteligente'}
          </Button>

          {matchMutation.isPending && (
            <Box sx={{ width: '100%', mt: 2 }}>
              <LinearProgress color="secondary" />
              <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
                A IA está analisando as descrições e sugerindo associações...
              </Typography>
            </Box>
          )}

          {matchMutation.isSuccess && (
            <Stack spacing={1} sx={{ mt: 2 }}>
              <Alert severity="info">
                Match concluído: {matchMutation.data.sugeridos} sugestões encontradas,{' '}
                {matchMutation.data.sem_match} itens sem correspondência.
              </Alert>
              <Button
                variant="contained"
                color="secondary"
                onClick={() => navigate(`/propostas/${id}/match-review`)}
              >
                Revisar e Confirmar Match ({matchMutation.data.sugeridos} sugestões)
              </Button>
            </Stack>
          )}
        </Paper>
      </Stack>
    </>
  );
}
