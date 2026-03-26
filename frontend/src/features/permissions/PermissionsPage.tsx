import { Stack } from '@mui/material';

import { ContractNotice } from '../../shared/components/ContractNotice';
import { PageHeader } from '../../shared/components/PageHeader';

export function PermissionsPage() {
  return (
    <>
      <PageHeader
        title="Permissões"
        description="Área reservada à administração de RBAC por cliente, preparada no frontend e explicitamente bloqueada até o backend expor os endpoints de manutenção."
      />

      <Stack spacing={2}>
        <ContractNotice
          title="RBAC de manutenção ainda não publicado"
          description="O backend já lê vínculos de usuário por cliente em /auth/me e nas dependências de autorização, mas ainda não há rotas para administrar esses vínculos via interface."
          missingContracts={[
            'GET /usuarios/{id}/perfis-cliente',
            'POST /usuarios/{id}/perfis-cliente',
            'DELETE /usuarios/{id}/perfis-cliente/{clienteId}/{perfil}',
          ]}
          availableNow={[
            'Leitura do RBAC efetivo via GET /auth/me',
            'Bloqueio de operações conforme RBAC no backend',
          ]}
        />
      </Stack>
    </>
  );
}
