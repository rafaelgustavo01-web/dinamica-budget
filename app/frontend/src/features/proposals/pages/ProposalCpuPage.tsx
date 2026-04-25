import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Paper, Stack, Typography, Button, Box, TextField, InputAdornment } from '@mui/material';
import ArrowBackOutlinedIcon from '@mui/icons-material/ArrowBackOutlined';
import CalculateOutlinedIcon from '@mui/icons-material/CalculateOutlined';

import { PageHeader } from '../../../shared/components/PageHeader';
import { CpuTable } from '../components/CpuTable';
import { ContractNotice } from '../../../shared/components/ContractNotice';

export function ProposalCpuPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [bdi, setBdi] = useState(25.0);

  return (
    <>
      <PageHeader
        title="Visualização de CPU"
        description="Detalhamento de custos da proposta com aplicação de BDI."
        actions={
          <Button
            variant="outlined"
            startIcon={<ArrowBackOutlinedIcon />}
            onClick={() => navigate(`/propostas/${id}`)}
          >
            Voltar
          </Button>
        }
      />

      <Stack spacing={3}>
        <Paper sx={{ p: 3 }}>
          <Stack direction="row" spacing={3} alignItems="center" sx={{ mb: 3 }}>
            <TextField
              label="BDI (%)"
              type="number"
              value={bdi}
              onChange={(e) => setBdi(parseFloat(e.target.value))}
              InputProps={{
                endAdornment: <InputAdornment position="end">%</InputAdornment>,
              }}
              sx={{ width: 150 }}
            />
            <Button
              variant="contained"
              startIcon={<CalculateOutlinedIcon />}
              disabled
            >
              Recalcular com BDI
            </Button>
          </Stack>

          <Box sx={{ filter: 'blur(2px)', pointerEvents: 'none', opacity: 0.6 }}>
             <Typography variant="body2" sx={{ mb: 2 }}>Exemplo de visualização (Aguardando contrato S-11)</Typography>
             <CpuTable itens={[]} />
          </Box>
        </Paper>

        <ContractNotice
          title="Endpoint de Geração de CPU Pendente"
          description="A visualização detalhada de CPU depende da conclusão da Sprint S-11 no backend."
          missingContracts={[
            `GET /propostas/${id}/cpu/itens`,
            `POST /propostas/${id}/cpu/gerar`
          ]}
          availableNow={[
            'CRUD de Proposta (S-09)',
            'Importação e Match (S-10)'
          ]}
        />
      </Stack>
    </>
  );
}
