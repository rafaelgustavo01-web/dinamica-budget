import { Stack } from '@mui/material';

import { ContractNotice } from '../../shared/components/ContractNotice';
import { PageHeader } from '../../shared/components/PageHeader';

export function ClientsPage() {
  return (
    <>
      <PageHeader
        title="Clientes"
        description="Estrutura pronta para o CRUD de clientes, aguardando a publicação dos contratos oficiais de backend."
      />

      <Stack spacing={2}>
        <ContractNotice
          title="Módulo bloqueado por contrato ausente"
          description="O domínio de clientes já existe no backend e no banco, mas o repositório atual ainda não publica rotas REST para listagem, cadastro, edição, ativação ou vínculos com usuários."
          missingContracts={[
            'GET /clientes',
            'POST /clientes',
            'PATCH /clientes/{id}',
            'PATCH /clientes/{id}/status',
            'GET /clientes/{id}/usuarios',
          ]}
        />
      </Stack>
    </>
  );
}
