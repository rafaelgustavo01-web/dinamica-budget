import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Stack,
  Tab,
  Tabs,
  Typography,
} from '@mui/material';
import EngineeringOutlinedIcon from '@mui/icons-material/EngineeringOutlined';
import HardwareOutlinedIcon from '@mui/icons-material/HardwareOutlined';
import LocalShippingOutlinedIcon from '@mui/icons-material/LocalShippingOutlined';
import SafetyDividerOutlinedIcon from '@mui/icons-material/SafetyDividerOutlined';
import SecurityOutlinedIcon from '@mui/icons-material/SecurityOutlined';
import WorkOutlineOutlinedIcon from '@mui/icons-material/WorkOutlineOutlined';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import TableChartOutlinedIcon from '@mui/icons-material/TableChartOutlined';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';

import { HelpTooltip } from '../../../shared/components/HelpTooltip';

import { PageHeader } from '../../../shared/components/PageHeader';
import { useFeedback } from '../../../shared/components/feedback/FeedbackProvider';
import { histogramaApi } from '../../../shared/services/api/histogramaApi';
import { proposalsApi } from '../../../shared/services/api/proposalsApi';
import { HistogramaTabMaoObra } from '../components/HistogramaTabMaoObra';
import { HistogramaTabGenerica } from '../components/HistogramaTabGenerica';
import { RecursosExtrasTab } from '../components/RecursosExtrasTab';

const TABS = [
  {
    id: 'mao-obra', label: 'Mão de Obra', icon: <EngineeringOutlinedIcon fontSize="small" />,
    help: 'Custos de mão de obra no snapshot desta proposta. Edite valores unitários conforme negociação.',
  },
  {
    id: 'equipamentos', label: 'Equipamentos', icon: <LocalShippingOutlinedIcon fontSize="small" />,
    help: 'Snapshot de custos de equipamentos com valores editáveis por proposta.',
  },
  {
    id: 'encargos', label: 'Encargos', icon: <WorkOutlineOutlinedIcon fontSize="small" />,
    help: 'Encargos trabalhistas em tabela única. Horista ou mensalista é atributo da linha.',
  },
  {
    id: 'epi', label: 'EPI / Uniforme', icon: <SecurityOutlinedIcon fontSize="small" />,
    help: 'Custo de EPIs e uniformes no snapshot desta proposta.',
  },
  {
    id: 'ferramentas', label: 'Ferramentas', icon: <HardwareOutlinedIcon fontSize="small" />,
    help: 'Custo de ferramentas e instrumentos no snapshot desta proposta.',
  },
  {
    id: 'mobilizacao', label: 'Mobilização', icon: <SafetyDividerOutlinedIcon fontSize="small" />,
    help: 'Custos de mobilização e desmobilização de equipes no snapshot desta proposta.',
  },
  {
    id: 'recursos-extras', label: 'Recursos Extras', icon: <AddCircleOutlineIcon fontSize="small" />,
    help: 'Adicione itens de custo não previstos na BCU base diretamente nesta proposta (materiais, terceiros, etc.).',
  },
];

export function HistogramaPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { showMessage } = useFeedback();
  const [activeTab, setActiveTab] = useState(0);

  const { data, isLoading, error } = useQuery({
    queryKey: ['histograma', id],
    queryFn: () => histogramaApi.getHistograma(id!),
    enabled: !!id,
  });

  const montarMutation = useMutation({
    mutationFn: () => histogramaApi.montarHistograma(id!),
    onSuccess: (counts) => {
      void queryClient.invalidateQueries({ queryKey: ['histograma', id] });
      void queryClient.invalidateQueries({ queryKey: ['proposta', id] });
      void queryClient.invalidateQueries({ queryKey: ['cpu-itens', id] });
      const total = Object.values(counts ?? {}).reduce((a, b) => a + Number(b ?? 0), 0);
      showMessage(`Histograma montado: ${total} itens.`);
    },
    onError: () => showMessage('Erro ao montar histograma.', 'error'),
  });

  const rebuildMutation = useMutation({
    mutationFn: () => proposalsApi.rebuild(id!),
    onSuccess: (result) => {
      void queryClient.invalidateQueries({ queryKey: ['proposta', id] });
      void queryClient.invalidateQueries({ queryKey: ['cpu-itens', id] });
      void queryClient.invalidateQueries({ queryKey: ['histograma', id] });
      showMessage(`CPU recalculada: ${result.itens_processados} itens processados.`);
    },
    onError: () => showMessage('Erro ao recalcular CPU.', 'error'),
  });

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">Erro ao carregar histograma.</Alert>;
  }

  if (!data) {
    return (
      <Box>
        <PageHeader
          title="Histograma da Proposta"
          description="Snapshot editável de custos por proposta."
        />
        <Paper sx={{ p: 6, textAlign: 'center' }}>
          <Button
            variant="contained"
            color="primary"
            onClick={() => montarMutation.mutate()}
            disabled={montarMutation.isPending}
          >
            {montarMutation.isPending ? 'Montando...' : 'Montar Histograma'}
          </Button>
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              O histograma ainda não foi montado para esta proposta. Clique em "Montar Histograma" para gerar o snapshot de custos.
            </Typography>
          </Box>
        </Paper>
      </Box>
    );
  }

  const hasDivergencias = data.divergencias.length > 0;

  return (
    <Box>
      <PageHeader
        title="Histograma da Proposta"
        description="Snapshot editável de custos por proposta. Edite valores, aceite atualizações da BCU e gerencie recursos extras."
      />

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems="center" sx={{ mb: 2 }}>
        <Button
          variant="contained"
          color="primary"
          onClick={() => montarMutation.mutate()}
          disabled={montarMutation.isPending}
        >
          {montarMutation.isPending ? 'Montando...' : 'Montar / Atualizar Histograma'}
        </Button>

        {data.cpu_desatualizada && (
          <>
            <Chip label="CPU Desatualizada" color="warning" variant="filled" />
            <Button
              variant="outlined"
              color="warning"
              size="small"
              startIcon={<TableChartOutlinedIcon />}
              onClick={() => rebuildMutation.mutate()}
              disabled={rebuildMutation.isPending}
            >
              {rebuildMutation.isPending ? 'Recalculando...' : 'Recalcular CPU'}
            </Button>
            <Button
              variant="text"
              size="small"
              onClick={() => navigate(`/propostas/${id}/cpu`)}
            >
              Ir para CPU
            </Button>
          </>
        )}

        {hasDivergencias && (
          <Chip
            label={`${data.divergencias.length} divergência(s) com BCU`}
            color="warning"
            variant="outlined"
          />
        )}

        <Box flex={1} />
      </Stack>

      <Tabs
        value={activeTab}
        onChange={(_, v) => setActiveTab(v)}
        variant="scrollable"
        scrollButtons="auto"
        sx={{
          borderBottom: 1,
          borderColor: 'divider',
          '& .MuiTab-root': { minHeight: 48, fontSize: '0.8rem' },
        }}
      >
        {TABS.map((tab) => (
          <Tab
            key={tab.id}
            icon={tab.icon}
            iconPosition="start"
            label={
              <>
                {tab.label}
                <HelpTooltip title={tab.help} />
              </>
            }
          />
        ))}
      </Tabs>

      <Box sx={{ py: 2 }}>
        {activeTab === 0 && (
          <HistogramaTabMaoObra
            propostaId={id!}
            items={data.mao_obra}
            divergencias={data.divergencias}
          />
        )}
        {activeTab === 1 && (
          <HistogramaTabGenerica
            propostaId={id!}
            tabela="equipamento"
            items={data.equipamentos}
            divergencias={data.divergencias}
            columns={[
              { key: 'aluguel_r_h', label: 'Aluguel R$/h', editable: true, numeric: true },
              { key: 'combustivel_r_h', label: 'Combust. R$/h', editable: true, numeric: true },
              { key: 'consumo_l_h', label: 'Consumo l/h', editable: true, numeric: true },
            ]}
          />
        )}
        {activeTab === 2 && (
          <HistogramaTabGenerica
            propostaId={id!}
            tabela="encargo"
            items={[...(data.encargos_horista ?? []), ...(data.encargos_mensalista ?? [])]}
            divergencias={data.divergencias}
            columns={[
              { key: 'tipo_encargo', label: 'Tipo', editable: false, numeric: false },
              { key: 'taxa_percent', label: 'Taxa %', editable: true, numeric: true },
              { key: 'grupo', label: 'Grupo', editable: false, numeric: false },
            ]}
          />
        )}
        {activeTab === 3 && (
          <HistogramaTabGenerica
            propostaId={id!}
            tabela="epi"
            items={data.epis}
            divergencias={data.divergencias}
            columns={[
              { key: 'custo_unitario', label: 'Custo Unit.', editable: true, numeric: true },
              { key: 'quantidade', label: 'Qtd', editable: true, numeric: true },
              { key: 'vida_util_meses', label: 'Vida Útil (meses)', editable: true, numeric: true },
            ]}
          />
        )}
        {activeTab === 4 && (
          <HistogramaTabGenerica
            propostaId={id!}
            tabela="ferramenta"
            items={data.ferramentas}
            divergencias={data.divergencias}
            columns={[
              { key: 'preco', label: 'Preço Unit.', editable: true, numeric: true },
              { key: 'quantidade', label: 'Qtd', editable: true, numeric: true },
            ]}
          />
        )}
        {activeTab === 5 && (
          <HistogramaTabGenerica
            propostaId={id!}
            tabela="mobilizacao"
            items={data.mobilizacao}
            divergencias={data.divergencias}
            columns={[
              { key: 'funcao', label: 'Função', editable: false, numeric: false },
              { key: 'tipo_mao_obra', label: 'Tipo MO', editable: false, numeric: false },
            ]}
          />
        )}
        {activeTab === 6 && <RecursosExtrasTab propostaId={id!} />}
      </Box>
    </Box>
  );
}
