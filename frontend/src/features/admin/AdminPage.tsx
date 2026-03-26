import BuildCircleOutlinedIcon from '@mui/icons-material/BuildCircleOutlined';
import {
  Alert,
  Button,
  CircularProgress,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import { useMutation } from '@tanstack/react-query';

import { PageHeader } from '../../shared/components/PageHeader';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { adminApi } from '../../shared/services/api/adminApi';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';

export function AdminPage() {
  const { showMessage } = useFeedback();

  const embeddingsMutation = useMutation({
    mutationFn: () => adminApi.computeEmbeddings(),
    onSuccess: (data) => {
      showMessage(`${data.embeddings_computados} embeddings recalculados.`);
    },
  });

  return (
    <>
      <PageHeader
        title="Administração"
        description="Área administrativa conectada somente às operações já publicadas pelo backend oficial."
      />

      <Stack direction={{ xs: 'column', xl: 'row' }} spacing={2}>
        <Paper sx={{ flex: 1, p: 3 }}>
          <Stack spacing={2}>
            <Stack direction="row" spacing={1.5} alignItems="center">
              <BuildCircleOutlinedIcon color="primary" />
              <Typography variant="h6">Sincronização de embeddings</Typography>
            </Stack>
            <Typography variant="body2" color="text.secondary">
              Dispara a operação administrativa existente em
              {' '}<strong>POST /admin/compute-embeddings</strong>.
            </Typography>
            <Button
              variant="contained"
              onClick={() => embeddingsMutation.mutate()}
              disabled={embeddingsMutation.isPending}
            >
              {embeddingsMutation.isPending ? (
                <CircularProgress size={20} color="inherit" />
              ) : (
                'Executar agora'
              )}
            </Button>
            {embeddingsMutation.data ? (
              <Alert severity="success">
                Resultado: {embeddingsMutation.data.embeddings_computados} itens processados.
              </Alert>
            ) : null}
            {embeddingsMutation.isError ? (
              <Alert severity="error">
                {extractApiErrorMessage(
                  embeddingsMutation.error,
                  'Falha ao executar a sincronização de embeddings.',
                )}
              </Alert>
            ) : null}
          </Stack>
        </Paper>

        <Paper sx={{ flex: 1, p: 3 }}>
          <Typography variant="h6" sx={{ mb: 1.5 }}>
            Escopo administrativo atual
          </Typography>
          <Stack spacing={1}>
            <Typography variant="body2" color="text.secondary">
              Gestão de usuários, clientes, permissões detalhadas e relatórios administrativos
              ainda exigem novos endpoints.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              O frontend já mantém essas áreas estruturadas, mas sem simular comportamento não
              suportado pelo backend.
            </Typography>
          </Stack>
        </Paper>
      </Stack>
    </>
  );
}
