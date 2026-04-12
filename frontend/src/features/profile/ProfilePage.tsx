import { zodResolver } from '@hookform/resolvers/zod';
import {
  Button,
  Chip,
  Divider,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { useAuth } from '../auth/AuthProvider';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import {
  errorMessages,
  successMessages,
} from '../../shared/components/FeedbackMessages';
import { PageHeader } from '../../shared/components/PageHeader';
import { authApi } from '../../shared/services/api/authApi';
import { getPerfilLabel } from '../../shared/utils/format';

/* ── Schemas ─────────────────────────────────────────────── */

const profileSchema = z.object({
  nome: z.string().min(2, 'O nome deve ter pelo menos 2 caracteres.'),
});
type ProfileFormValues = z.infer<typeof profileSchema>;

const passwordSchema = z
  .object({
    current_password: z.string().min(1, 'Informe a senha atual.'),
    new_password: z.string().min(8, 'A nova senha deve ter pelo menos 8 caracteres.'),
    confirm_password: z.string().min(1, 'Confirme a nova senha.'),
  })
  .refine((d) => d.new_password === d.confirm_password, {
    message: 'As senhas não coincidem.',
    path: ['confirm_password'],
  });
type PasswordFormValues = z.infer<typeof passwordSchema>;

/* ── Component ───────────────────────────────────────────── */

export function ProfilePage() {
  const { user, selectedClientId, refreshUser, logout } = useAuth();
  const { showMessage } = useFeedback();

  // ── Profile form ──
  const {
    register: registerProfile,
    handleSubmit: handleProfileSubmit,
    formState: { errors: profileErrors },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: { nome: user?.nome ?? '' },
  });

  const profileMutation = useMutation({
    mutationFn: (values: ProfileFormValues) => authApi.updateProfile(values),
    onSuccess: () => {
      showMessage(successMessages.profileUpdated);
      refreshUser().catch(() => {});
    },
    onError: () => showMessage(errorMessages.profileUpdate),
  });

  // ── Password form ──
  const {
    register: registerPassword,
    handleSubmit: handlePasswordSubmit,
    formState: { errors: passwordErrors },
    reset: resetPasswordForm,
  } = useForm<PasswordFormValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: { current_password: '', new_password: '', confirm_password: '' },
  });

  const passwordMutation = useMutation({
    mutationFn: (values: PasswordFormValues) =>
      authApi.changePassword({
        current_password: values.current_password,
        new_password: values.new_password,
      }),
    onSuccess: () => {
      showMessage(successMessages.passwordChanged);
      resetPasswordForm();
      // Force re-login since refresh tokens were revoked
      logout().catch(() => {});
    },
    onError: () => showMessage(errorMessages.passwordChange),
  });

  return (
    <>
      <PageHeader
        title="Meu Perfil"
        description="Visualize e edite seus dados de acesso, perfis por cliente e troque sua senha."
      />

      <Stack direction={{ xs: 'column', xl: 'row' }} spacing={2}>
        {/* ── Identidade (read-only) ── */}
        <Paper sx={{ flex: 1, p: 3, border: '1px solid', borderColor: 'divider' }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Identidade
          </Typography>
          <Stack spacing={1.2}>
            <Typography variant="body2" color="text.secondary">
              Nome: {user?.nome}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              E-mail: {user?.email}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Status: {user?.is_active ? 'Ativo' : 'Inativo'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Escopo administrativo: {user?.is_admin ? 'Sim' : 'Não'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Cliente em contexto: {selectedClientId || 'Nenhum'}
            </Typography>
          </Stack>
        </Paper>

        {/* ── Perfis por cliente ── */}
        <Paper sx={{ flex: 1, p: 3, border: '1px solid', borderColor: 'divider' }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Perfis por cliente
          </Typography>
          <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
            {user?.perfis.map((perfil) => (
              <Chip
                key={`${perfil.cliente_id}:${perfil.perfil}`}
                label={`${getPerfilLabel(perfil.perfil)} · ${perfil.cliente_id}`}
                variant="outlined"
              />
            ))}
          </Stack>
        </Paper>
      </Stack>

      <Divider sx={{ my: 3 }} />

      <Stack direction={{ xs: 'column', xl: 'row' }} spacing={2}>
        {/* ── Editar nome ── */}
        <Paper sx={{ flex: 1, p: 3, border: '1px solid', borderColor: 'divider' }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Editar perfil
          </Typography>
          <Stack
            component="form"
            spacing={2}
            onSubmit={handleProfileSubmit((v) => profileMutation.mutate(v))}
          >
            <TextField
              label="Nome"
              fullWidth
              error={Boolean(profileErrors.nome)}
              helperText={profileErrors.nome?.message}
              {...registerProfile('nome')}
            />
            <Button
              type="submit"
              variant="contained"
              disabled={profileMutation.isPending}
            >
              {profileMutation.isPending ? 'Salvando...' : 'Salvar alterações'}
            </Button>
          </Stack>
        </Paper>

        {/* ── Trocar senha ── */}
        <Paper sx={{ flex: 1, p: 3, border: '1px solid', borderColor: 'divider' }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Trocar senha
          </Typography>
          <Stack
            component="form"
            spacing={2}
            onSubmit={handlePasswordSubmit((v) => passwordMutation.mutate(v))}
          >
            <TextField
              label="Senha atual"
              type="password"
              fullWidth
              error={Boolean(passwordErrors.current_password)}
              helperText={passwordErrors.current_password?.message}
              {...registerPassword('current_password')}
            />
            <TextField
              label="Nova senha"
              type="password"
              fullWidth
              error={Boolean(passwordErrors.new_password)}
              helperText={passwordErrors.new_password?.message}
              {...registerPassword('new_password')}
            />
            <TextField
              label="Confirmar nova senha"
              type="password"
              fullWidth
              error={Boolean(passwordErrors.confirm_password)}
              helperText={passwordErrors.confirm_password?.message}
              {...registerPassword('confirm_password')}
            />
            <Button
              type="submit"
              variant="contained"
              color="warning"
              disabled={passwordMutation.isPending}
            >
              {passwordMutation.isPending ? 'Alterando...' : 'Alterar senha'}
            </Button>
          </Stack>
        </Paper>
      </Stack>
    </>
  );
}
