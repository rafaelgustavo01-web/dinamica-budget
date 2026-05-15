import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import RefreshIcon from '@mui/icons-material/Refresh';
import { Alert, Box, Button, Paper, Stack, Typography } from '@mui/material';
import { ErrorBoundary, type FallbackProps } from 'react-error-boundary';

function AppErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  if (import.meta.env.DEV) {
    console.error(error);
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        p: 3,
        bgcolor: 'background.default',
      }}
    >
      <Paper sx={{ p: 3, maxWidth: 560, width: '100%' }}>
        <Stack spacing={2}>
          <Stack direction="row" spacing={1.5} alignItems="center">
            <ErrorOutlineIcon color="error" />
            <Typography variant="h6">Erro inesperado na interface</Typography>
          </Stack>
          <Alert severity="error">
            A tela encontrou um erro local. Recarregue a página e, se persistir,
            use o console do navegador para ver o detalhe técnico.
          </Alert>
          {import.meta.env.DEV && error instanceof Error ? (
            <Typography
              component="pre"
              variant="caption"
              sx={{
                m: 0,
                p: 1.5,
                bgcolor: 'action.hover',
                borderRadius: 1,
                overflow: 'auto',
                whiteSpace: 'pre-wrap',
              }}
            >
              {error.message}
            </Typography>
          ) : null}
          <Button
            variant="contained"
            startIcon={<RefreshIcon />}
            onClick={resetErrorBoundary}
            sx={{ alignSelf: 'flex-start' }}
          >
            Tentar novamente
          </Button>
        </Stack>
      </Paper>
    </Box>
  );
}

export function AppErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary FallbackComponent={AppErrorFallback}>
      {children}
    </ErrorBoundary>
  );
}
