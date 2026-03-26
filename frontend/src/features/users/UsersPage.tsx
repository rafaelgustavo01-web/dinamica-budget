import {
  Alert,
  Button,
  CircularProgress,
  Checkbox,
  FormControlLabel,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { useState } from 'react';
import { z } from 'zod';

import { ContractNotice } from '../../shared/components/ContractNotice';
import { PageHeader } from '../../shared/components/PageHeader';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import { userApi } from '../../shared/services/api/userApi';
import type { UsuarioResponse } from '../../shared/types/contracts/auth';

const createUserSchema = z.object({
  nome: z.string().min(3, 'Informe o nome completo.'),
  email: z.email('Informe um email válido.'),
  password: z.string().min(6, 'Use ao menos 6 caracteres.'),
  is_admin: z.boolean(),
});

type CreateUserFormValues = z.infer<typeof createUserSchema>;

export function UsersPage() {
  const { showMessage } = useFeedback();
  const [createdUser, setCreatedUser] = useState<UsuarioResponse | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<CreateUserFormValues>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      nome: '',
      email: '',
      password: '',
      is_admin: false,
    },
  });

  const createUserMutation = useMutation({
    mutationFn: userApi.create,
    onSuccess: (data) => {
      setCreatedUser(data);
      showMessage('Usuário criado com sucesso.');
      reset();
    },
  });

  return (
    <>
      <PageHeader
        title="Usuários"
        description="Cadastro administrativo conectado ao endpoint oficial já publicado, com transparência sobre o que ainda falta para o CRUD completo."
      />

      <Stack direction={{ xs: 'column', xl: 'row' }} spacing={2}>
        <Paper sx={{ flex: 1, p: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Novo usuário
          </Typography>
          <Stack
            component="form"
            spacing={2}
            onSubmit={handleSubmit((values) => createUserMutation.mutate(values))}
          >
            <TextField
              label="Nome"
              error={Boolean(errors.nome)}
              helperText={errors.nome?.message}
              {...register('nome')}
            />
            <TextField
              label="Email"
              type="email"
              error={Boolean(errors.email)}
              helperText={errors.email?.message}
              {...register('email')}
            />
            <TextField
              label="Senha inicial"
              type="password"
              error={Boolean(errors.password)}
              helperText={errors.password?.message}
              {...register('password')}
            />
            <FormControlLabel
              control={<Checkbox {...register('is_admin')} />}
              label="Usuário administrativo"
            />
            <Button
              type="submit"
              variant="contained"
              disabled={createUserMutation.isPending}
            >
              {createUserMutation.isPending ? (
                <CircularProgress size={20} color="inherit" />
              ) : (
                'Criar usuário'
              )}
            </Button>
            {createUserMutation.isError ? (
              <Alert severity="error">
                {extractApiErrorMessage(
                  createUserMutation.error,
                  'Falha ao criar o usuário.',
                )}
              </Alert>
            ) : null}
          </Stack>
        </Paper>

        <Paper sx={{ flex: 1, p: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Último cadastro confirmado
          </Typography>
          {createdUser ? (
            <Stack spacing={1}>
              <Typography variant="body2" color="text.secondary">
                Nome: {createdUser.nome}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Email: {createdUser.email}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Admin: {createdUser.is_admin ? 'Sim' : 'Não'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Ativo: {createdUser.is_active ? 'Sim' : 'Não'}
              </Typography>
            </Stack>
          ) : (
            <Typography variant="body2" color="text.secondary">
              Nenhum cadastro realizado nesta sessão.
            </Typography>
          )}
        </Paper>
      </Stack>

      <Stack spacing={2} sx={{ mt: 2 }}>
        <ContractNotice
          title="CRUD completo de usuários ainda não está exposto"
          description="Hoje o backend publica somente o cadastro de usuário. Listagem, edição, ativação/inativação e vínculos por cliente continuam ausentes como endpoint oficial."
          missingContracts={[
            'GET /usuarios',
            'PATCH /usuarios/{id}',
            'PATCH /usuarios/{id}/status',
            'GET/PUT /usuarios/{id}/perfis-cliente',
          ]}
          availableNow={['POST /auth/usuarios']}
        />
      </Stack>
    </>
  );
}
