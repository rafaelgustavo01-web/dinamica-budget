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
  email: z.email('Informe um email valido.'),
  password: z.string().min(8, 'Use ao menos 8 caracteres.'),
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
      showMessage('Usuario criado com sucesso.');
      reset();
    },
  });

  return (
    <>
      <PageHeader
        title="Usuarios"
        description="Fluxo administrativo protegido para cadastro de usuarios, dependente de autenticacao e privilegio administrativo no backend."
      />

      <Stack direction={{ xs: 'column', xl: 'row' }} spacing={2}>
        <Paper sx={{ flex: 1, p: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Novo usuario
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Esta operacao usa o endpoint administrativo POST /auth/usuarios e nao faz parte do fluxo operacional comum.
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
              helperText={errors.password?.message ?? 'Use ao menos 8 caracteres.'}
              {...register('password')}
            />
            <FormControlLabel
              control={<Checkbox {...register('is_admin')} />}
              label="Usuario administrativo"
            />
            <Button
              type="submit"
              variant="contained"
              disabled={createUserMutation.isPending}
            >
              {createUserMutation.isPending ? (
                <CircularProgress size={20} color="inherit" />
              ) : (
                'Criar usuario'
              )}
            </Button>
            {createUserMutation.isError ? (
              <Alert severity="error">
                {extractApiErrorMessage(
                  createUserMutation.error,
                  'Falha ao criar o usuario.',
                )}
              </Alert>
            ) : null}
          </Stack>
        </Paper>

        <Paper sx={{ flex: 1, p: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Ultimo cadastro administrativo confirmado
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
                Admin: {createdUser.is_admin ? 'Sim' : 'Nao'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Ativo: {createdUser.is_active ? 'Sim' : 'Nao'}
              </Typography>
            </Stack>
          ) : (
            <Typography variant="body2" color="text.secondary">
              Nenhum cadastro realizado nesta sessao.
            </Typography>
          )}
        </Paper>
      </Stack>

      <Stack spacing={2} sx={{ mt: 2 }}>
        <ContractNotice
          title="Fluxo administrativo parcial e protegido"
          description="A tela cobre somente o cadastro administrativo autenticado via POST /auth/usuarios. Listagem, edicao, ativacao/inativacao e vinculos por cliente continuam dependentes de contratos REST ainda nao publicados."
          missingContracts={[
            'GET /usuarios',
            'PATCH /usuarios/{id}',
            'PATCH /usuarios/{id}/status',
            'GET/PUT /usuarios/{id}/perfis-cliente',
          ]}
          availableNow={[
            'POST /auth/usuarios',
            'Acesso exposto apenas na area administrativa autenticada',
          ]}
        />
      </Stack>
    </>
  );
}
