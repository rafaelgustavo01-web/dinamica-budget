import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { useLocation, useNavigate } from 'react-router-dom';
import { z } from 'zod';

import { useAuth } from './AuthProvider';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';

const loginSchema = z.object({
  email: z.email('Informe um email válido.'),
  password: z.string().min(1, 'Informe a senha.'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export function LoginPage() {
  const { login } = useAuth();
  const { showMessage } = useFeedback();
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = (location.state as { from?: string } | null)?.from ?? '/dashboard';

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      showMessage('Sessão iniciada com sucesso.');
      navigate(redirectTo, { replace: true });
    },
  });

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', lg: '1.15fr 0.85fr' },
        background:
          'linear-gradient(135deg, #0f1720 0%, #153242 42%, #f3f5f7 42%, #f3f5f7 100%)',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'flex-end',
          px: { xs: 3, md: 6 },
          py: { xs: 4, md: 6 },
        }}
      >
        <Stack spacing={2.5} sx={{ maxWidth: 560, color: 'common.white' }}>
          <Typography variant="overline" sx={{ color: 'rgba(255,255,255,0.64)' }}>
            Dinamica Budget
          </Typography>
          <Typography variant="h1" sx={{ fontSize: { xs: '2.2rem', md: '3.6rem' } }}>
            Operação orçamentária com fluxo rastreável e aderente ao backend.
          </Typography>
          <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.78)' }}>
            Catálogo, busca inteligente, homologação, governança e RBAC por cliente em uma
            interface interna preparada para intranet.
          </Typography>
        </Stack>
      </Box>

      <Box
        sx={{
          display: 'grid',
          placeItems: 'center',
          px: 3,
          py: 4,
        }}
      >
        <Paper sx={{ width: '100%', maxWidth: 460, p: { xs: 3, md: 4 } }}>
          <Stack spacing={3}>
            <Stack direction="row" spacing={1.5} alignItems="center">
              <Box
                sx={{
                  width: 44,
                  height: 44,
                  borderRadius: 2.5,
                  display: 'grid',
                  placeItems: 'center',
                  backgroundColor: 'primary.main',
                  color: 'common.white',
                }}
              >
                <LockOutlinedIcon />
              </Box>
              <div>
                <Typography variant="h5">Acessar sistema</Typography>
                <Typography variant="body2" color="text.secondary">
                  Autenticação integrada ao backend oficial.
                </Typography>
              </div>
            </Stack>

            {loginMutation.isError ? (
              <Alert severity="error">
                {extractApiErrorMessage(
                  loginMutation.error,
                  'Não foi possível autenticar no momento.',
                )}
              </Alert>
            ) : null}

            <Stack
              component="form"
              spacing={2}
              onSubmit={handleSubmit((values) => loginMutation.mutate(values))}
            >
              <TextField
                label="Usuário ou email"
                type="email"
                autoComplete="username"
                error={Boolean(errors.email)}
                helperText={errors.email?.message}
                {...register('email')}
              />
              <TextField
                label="Senha"
                type="password"
                autoComplete="current-password"
                error={Boolean(errors.password)}
                helperText={errors.password?.message}
                {...register('password')}
              />

              <Button
                type="submit"
                variant="contained"
                size="large"
                disabled={loginMutation.isPending}
              >
                {loginMutation.isPending ? (
                  <CircularProgress size={20} color="inherit" />
                ) : (
                  'Entrar'
                )}
              </Button>
            </Stack>
          </Stack>
        </Paper>
      </Box>
    </Box>
  );
}
