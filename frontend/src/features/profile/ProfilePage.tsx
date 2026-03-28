import { Chip, Paper, Stack, Typography } from '@mui/material';

import { useAuth } from '../auth/AuthProvider';
import { ContractNotice } from '../../shared/components/ContractNotice';
import { PageHeader } from '../../shared/components/PageHeader';
import { getPerfilLabel } from '../../shared/utils/format';

export function ProfilePage() {
  const { user, selectedClientId } = useAuth();

  return (
    <>
      <PageHeader
        title="Meu Perfil"
        description="Visualize seus dados de acesso, perfis por cliente e o estado atual da sessão autenticada."
      />

      <Stack direction={{ xs: 'column', xl: 'row' }} spacing={2}>
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

      <Stack spacing={2} sx={{ mt: 2 }}>
        <ContractNotice
          title="Edição de perfil ainda depende de contrato"
          description="O backend atual expõe leitura de /auth/me, login, refresh e logout, mas ainda não publicou rotas para edição de dados pessoais, troca de senha ou preferências operacionais."
          missingContracts={[
            'PATCH /auth/me ou /perfil',
            'POST /auth/trocar-senha',
            'GET/PATCH /perfil/preferencias',
          ]}
          availableNow={[
            'Leitura do contexto autenticado via GET /auth/me',
            'Logout transacional via POST /auth/logout',
          ]}
        />
      </Stack>
    </>
  );
}
