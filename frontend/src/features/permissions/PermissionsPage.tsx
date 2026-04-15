import { Stack } from '@mui/material';

import { ContractNotice } from '../../shared/components/ContractNotice';
import { PageHeader } from '../../shared/components/PageHeader';

export function PermissionsPage() {
  return (
    <>
      <PageHeader
        title="Permissões"
        description="A gestão operacional de perfis por cliente já foi integrada ao módulo Usuários. Esta área dedicada segue fora do menu principal até existir um fluxo separado no backend."
      />

      <Stack spacing={2}>
        <ContractNotice
          title="Fluxo dedicado ainda não separado"
          description="Os contratos GET e PUT de perfis por cliente já estão operacionais, mas a manutenção de RBAC continua centralizada em Usuários."
          missingContracts={[
            'Contrato dedicado para administração separada de permissões',
            'Listagens e filtros próprios para governança de RBAC',
          ]}
          availableNow={[
            'GET /usuarios/{id}/perfis-cliente via Usuários',
            'PUT /usuarios/{id}/perfis-cliente via Usuários',
          ]}
        />
      </Stack>
    </>
  );
}
