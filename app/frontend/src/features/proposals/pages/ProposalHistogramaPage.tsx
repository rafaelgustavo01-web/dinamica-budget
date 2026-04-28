import { Box, Paper, Typography, CircularProgress, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { PageHeader } from '../../../shared/components/PageHeader';
import { histogramaApi } from '../../../shared/services/api/histogramaApi';

export function HistogramaPage() {
  const { id } = useParams<{ id: string }>();

  const { data, isLoading, error } = useQuery({
    queryKey: ['histograma', id],
    queryFn: () => histogramaApi.getHistograma(id!),
    enabled: !!id,
  });

  if (isLoading) return <CircularProgress />;
  if (error) return <Typography color="error">Erro ao carregar histograma</Typography>;
  if (!data) return null;

  return (
    <Box>
      <PageHeader title="Histograma da Proposta" description={`Visualização e edição do snapshot de custos da proposta`} />
      
      {data.cpu_desatualizada && (
        <Typography color="warning.main" sx={{ mb: 2 }}>
          ⚠️ CPU desatualizada. Lembre-se de recalcular a CPU para aplicar estas mudanças.
        </Typography>
      )}

      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Mão de Obra ({data.mao_obra.length})</Typography>
        </AccordionSummary>
        <AccordionDetails>
          {data.mao_obra.map((item) => (
            <Paper key={item.id} sx={{ p: 2, mb: 1 }}>
              <Typography variant="body1">
                <strong>{item.descricao_funcao}</strong> - Custo/h: {item.custo_unitario_h} {item.editado_manualmente && '(Editado)'}
              </Typography>
            </Paper>
          ))}
        </AccordionDetails>
      </Accordion>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Equipamentos ({data.equipamentos.length})</Typography>
        </AccordionSummary>
        <AccordionDetails>
          {data.equipamentos.map((item) => (
            <Paper key={item.id} sx={{ p: 2, mb: 1 }}>
              <Typography variant="body1">
                <strong>{item.equipamento}</strong> - Aluguel/h: {item.aluguel_r_h} {item.editado_manualmente && '(Editado)'}
              </Typography>
            </Paper>
          ))}
        </AccordionDetails>
      </Accordion>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Encargos ({data.encargos_horista.length + data.encargos_mensalista.length})</Typography>
        </AccordionSummary>
        <AccordionDetails>
          {data.encargos_horista.map((item) => (
            <Paper key={item.id} sx={{ p: 2, mb: 1 }}>
              <Typography variant="body1">
                <strong>{item.discriminacao_encargo}</strong> - Taxa: {item.taxa_percent}% {item.editado_manualmente && '(Editado)'}
              </Typography>
            </Paper>
          ))}
        </AccordionDetails>
      </Accordion>

      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Recursos Extras ({data.recursos_extras.length})</Typography>
        </AccordionSummary>
        <AccordionDetails>
          {data.recursos_extras.map((item) => (
            <Paper key={item.id} sx={{ p: 2, mb: 1 }}>
              <Typography variant="body1">
                <strong>{item.descricao}</strong> ({item.tipo_recurso}) - Custo Unitário: {item.custo_unitario}
              </Typography>
            </Paper>
          ))}
        </AccordionDetails>
      </Accordion>
      
    </Box>
  );
}
