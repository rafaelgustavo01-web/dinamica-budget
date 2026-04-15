import BuildCircleOutlinedIcon from '@mui/icons-material/BuildCircleOutlined';
import { Alert, Button, CircularProgress, Paper, Stack, Typography } from '@mui/material';
import { useMutation } from '@tanstack/react-query';

import {
  errorMessages,
  infoMessages,
  successMessages,
} from '../../shared/components/FeedbackMessages';
import { PageHeader } from '../../shared/components/PageHeader';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { adminApi } from '../../shared/services/api/adminApi';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';

export function AdminPage() {
  const { showMessage } = useFeedback();

  const embeddingsMutation = useMutation({
    mutationFn: () => adminApi.computeEmbeddings(),
    onSuccess: () => {
      showMessage(successMessages.embeddingsProcessed);
    },
  });

  return (
    <>
      <PageHeader
        title="Administração"
        description="Configurações avançadas do sistema. Área restrita a administradores."
      />

      <Stack direction={{ xs: 'column', xl: 'row' }} spacing={2}>
        <Paper sx={{ flex: 1, p: 3, border: '1px solid', borderColor: 'divider' }}>
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

        <Paper sx={{ flex: 1, p: 3, border: '1px solid', borderColor: 'divider' }}>
          <Typography variant="h6" sx={{ mb: 1.5 }}>
            Escopo administrativo atual
          </Typography>
          <Stack spacing={1}>
            <Typography variant="body2" color="text.secondary">
              Gestão de usuários e clientes já opera com contratos administrativos publicados.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              O módulo próprio de permissões, a autoedição de perfil e relatórios dedicados
              continuam dependentes de novos endpoints do backend.
            </Typography>
          </Stack>
        </Paper>
      </Stack>
    </>
  );
}
