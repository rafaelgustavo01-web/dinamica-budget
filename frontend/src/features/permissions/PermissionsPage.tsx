import { Stack } from '@mui/material';

import { ContractNotice } from '../../shared/components/ContractNotice';
import { PageHeader } from '../../shared/components/PageHeader';

export function PermissionsPage() {
  return (
    <>
      <PageHeader
        title="Permissoes"
        description="A gestao operacional de perfis por cliente ja foi integrada ao modulo Usuarios. Esta area dedicada segue fora do menu principal ate existir um fluxo separado no backend."
      />

      <Stack spacing={2}>
        <ContractNotice
          title="Fluxo dedicado ainda nao separado"
          description="Os contratos `GET/PUT /usuarios/{id}/perfis-cliente` ja estao operacionais, mas a manutencao de RBAC foi centralizada em Usuarios. Um modulo dedicado de Permissoes continua sem contrato proprio suficiente para voltar ao menu."
          missingContracts={[
            'Contrato dedicado para administracao separada de permissoes',
            'Listagens e filtros proprios para governanca de RBAC',
          ]}
          availableNow={[
            'GET /usuarios/{id}/perfis-cliente via Usuarios',
            'PUT /usuarios/{id}/perfis-cliente via Usuarios',
          ]}
        />
      </Stack>
    </>
  );
}
