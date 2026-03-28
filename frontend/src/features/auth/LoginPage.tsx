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

import { errorMessages, successMessages } from '../../shared/components/FeedbackMessages';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import { useAuth } from './AuthProvider';

const loginSchema = z.object({
  email: z.email('Informe um e-mail válido.'),
  password: z.string().min(1, 'Informe sua senha.'),
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
      showMessage(successMessages.login);
      navigate(redirectTo, { replace: true });
    },
  });

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', lg: '1.05fr 0.95fr' },
      }}
    >
      <Box
        sx={{
          position: 'relative',
          overflow: 'hidden',
          display: { xs: 'none', lg: 'flex' },
          alignItems: 'flex-end',
          px: 6,
          py: 6,
          background:
            'linear-gradient(145deg, rgba(14,21,37,1) 0%, rgba(27,42,74,1) 42%, rgba(27,58,107,1) 100%)',
          '&::before': {
            content: '""',
            position: 'absolute',
            right: -48,
            top: 72,
            width: 260,
            height: 260,
            borderRadius: 10,
            border: '18px solid rgba(255,255,255,0.08)',
            transform: 'rotate(45deg)',
          },
          '&::after': {
            content: '""',
            position: 'absolute',
            left: -40,
            top: -32,
            width: 220,
            height: 220,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(232,166,35,0.26), transparent 70%)',
          },
        }}
      >
        <Stack spacing={2.5} sx={{ maxWidth: 580, color: 'common.white', position: 'relative' }}>
          <Box
            sx={{
              width: 64,
              height: 6,
              borderRadius: 999,
              backgroundColor: 'secondary.main',
            }}
          />
          <Typography variant="overline" sx={{ color: 'rgba(255,255,255,0.7)' }}>
            Construtora Dinâmica
          </Typography>
          <Typography variant="h1" sx={{ fontSize: '3.4rem' }}>
            Orçamentação inteligente com rastreabilidade e controle.
          </Typography>
          <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.8)', maxWidth: 520 }}>
            Catálogo híbrido, busca inteligente, homologação e composições em uma camada
            operacional pensada para equipes técnicas.
          </Typography>
          <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.62)', maxWidth: 520 }}>
            Acesse com seu e-mail corporativo e continue o trabalho no contexto do cliente
            selecionado.
          </Typography>
        </Stack>
      </Box>

      <Box
        sx={{
          display: 'grid',
          placeItems: 'center',
          px: { xs: 3, md: 4 },
          py: { xs: 4, md: 5 },
        }}
      >
        <Paper
          sx={{
            width: '100%',
            maxWidth: 460,
            p: { xs: 3, md: 4 },
            border: '1px solid',
            borderColor: 'divider',
            boxShadow: 12,
          }}
        >
          <Stack spacing={3}>
            <Stack direction="row" spacing={1.5} alignItems="center">
              <Box
                sx={{
                  width: 44,
                  height: 44,
                  borderRadius: 2.5,
                  display: 'grid',
                  placeItems: 'center',
                  background:
                    'linear-gradient(135deg, rgba(27,58,107,1) 0%, rgba(36,54,96,1) 100%)',
                  color: 'common.white',
                  boxShadow: '0 10px 20px rgba(27,58,107,0.18)',
                }}
              >
                <LockOutlinedIcon />
              </Box>
              <div>
                <Typography variant="h5">Entrar</Typography>
                <Typography variant="body2" color="text.secondary">
                  Informe seu e-mail e sua senha para acessar o sistema.
                </Typography>
              </div>
            </Stack>

            {loginMutation.isError ? (
              <Alert severity="error">
                {extractApiErrorMessage(loginMutation.error, errorMessages.login)}
              </Alert>
            ) : null}

            <Stack
              component="form"
              spacing={2}
              onSubmit={handleSubmit((values) => loginMutation.mutate(values))}
            >
              <TextField
                label="E-mail"
                type="email"
                autoComplete="username"
                placeholder="nome@empresa.com.br"
                error={Boolean(errors.email)}
                helperText={errors.email?.message}
                {...register('email')}
              />
              <TextField
                label="Senha"
                type="password"
                autoComplete="current-password"
                placeholder="Digite sua senha"
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
