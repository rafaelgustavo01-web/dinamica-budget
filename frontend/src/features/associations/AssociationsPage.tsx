import { Stack } from '@mui/material';

import { ContractNotice } from '../../shared/components/ContractNotice';
import { PageHeader } from '../../shared/components/PageHeader';

export function AssociationsPage() {
  return (
    <>
      <PageHeader
        title="Associações"
        description="Módulo estruturado para operar a trilha de associações inteligentes, mas ainda sem endpoint oficial de leitura, exclusão ou edição controlada."
      />

      <Stack spacing={2}>
        <ContractNotice
          title="Frontend preparado, contrato ainda ausente"
          description="O backend já possui repositório de associações com listagem por cliente, mas essa capacidade ainda não foi publicada por endpoint. O frontend não simula leitura ou exclusão fora do contrato oficial."
          missingContracts={[
            'GET /associacoes',
            'DELETE /associacoes/{id}',
            'PATCH /associacoes/{id}',
          ]}
          availableNow={[
            'Criação/fortalecimento via POST /busca/associar',
          ]}
        />
      </Stack>
    </>
  );
}
