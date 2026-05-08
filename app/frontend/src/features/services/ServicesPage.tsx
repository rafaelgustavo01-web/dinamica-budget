import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import {
  Alert,
  Button,
  Chip,
  CircularProgress,
  Collapse,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { useState } from 'react';
import { z } from 'zod';

import { EmptyState } from '../../shared/components/EmptyState';
import {
  errorMessages,
  successMessages,
} from '../../shared/components/FeedbackMessages';
import { PageHeader } from '../../shared/components/PageHeader';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import { servicesApi } from '../../shared/services/api/servicesApi';
import type { ServicoTcpoResponse } from '../../shared/types/contracts/servicos';
import { formatCurrency, toNumber } from '../../shared/utils/format';
import { useAuth } from '../auth/AuthProvider';

const createServiceSchema = z.object({
  codigo_origem: z.string().min(1, 'Informe o código do serviço.'),
  descricao: z.string().min(3, 'Informe a descrição do serviço.'),
  unidade_medida: z.string().min(1, 'Informe a unidade.'),
  custo_unitario: z.coerce.number().positive('Informe um custo maior que zero.'),
  categoria_id: z.string().optional(),
});

type CreateServiceFormInput = z.input<typeof createServiceSchema>;
type CreateServiceFormOutput = z.output<typeof createServiceSchema>;

const TIPO_RECURSO_LABEL: Record<string, string> = {
  MO: 'Mão de Obra',
  INSUMO: 'Insumo',
  FERRAMENTA: 'Ferramenta',
  EQUIPAMENTO: 'Equipamento',
  SERVICO: 'Serviço',
};

function ComposicaoRow({ servicoId }: { servicoId: string }) {
  const componentesQuery = useQuery({
    queryKey: ['services', 'componentes', servicoId],
    queryFn: () => servicesApi.getComponentes(servicoId),
    staleTime: 5 * 60 * 1000,
  });

  if (componentesQuery.isLoading) {
    return (
      <TableRow>
        <TableCell colSpan={5} sx={{ pl: 8 }}>
          <CircularProgress size={16} sx={{ mr: 1 }} />
          <Typography variant="caption" color="text.secondary">
            Carregando composição...
          </Typography>
        </TableCell>
      </TableRow>
    );
  }

  if (componentesQuery.isError || !componentesQuery.data) {
    return (
      <TableRow>
        <TableCell colSpan={5} sx={{ pl: 8 }}>
          <Typography variant="caption" color="error">
            Erro ao carregar composição.
          </Typography>
        </TableCell>
      </TableRow>
    );
  }

  if (componentesQuery.data.length === 0) {
    return (
      <TableRow>
        <TableCell colSpan={5} sx={{ pl: 8 }}>
          <Typography variant="caption" color="text.secondary">
            Sem componentes na composição.
          </Typography>
        </TableCell>
      </TableRow>
    );
  }

  const totalComposicao = componentesQuery.data.reduce(
    (acc, item) => {
      if (item.custo_total == null) {
        return acc;
      }
      const custoTotal = toNumber(item.custo_total);
      return Number.isFinite(custoTotal) ? acc + custoTotal : acc;
    },
    0,
  );

  return (
    <>
      {componentesQuery.data.map((item) => (
        <TableRow key={item.id} sx={{ bgcolor: 'action.hover' }}>
          <TableCell sx={{ width: 48 }} />
          <TableCell sx={{ pl: 5 }}>
            <Typography variant="caption" color="text.secondary">
              {item.codigo_origem ?? '—'}
            </Typography>
          </TableCell>
          <TableCell>
            <Stack direction="row" spacing={1} alignItems="center">
              <Typography variant="body2">{item.descricao_filho}</Typography>
              {item.tipo_recurso && item.tipo_recurso !== 'SERVICO' ? (
                <Chip
                  label={TIPO_RECURSO_LABEL[item.tipo_recurso] ?? item.tipo_recurso}
                  size="small"
                  variant="outlined"
                  sx={{ fontSize: 10, height: 18 }}
                />
              ) : null}
            </Stack>
          </TableCell>
          <TableCell>
            <Typography variant="caption">{item.unidade_medida}</Typography>
          </TableCell>
          <TableCell align="right">
            <Stack alignItems="flex-end">
              <Typography variant="caption" color="text.secondary">
                {String(item.quantidade_consumo)} × {formatCurrency(item.custo_unitario)}
              </Typography>
              <Typography variant="caption" fontWeight={600}>
                {formatCurrency(item.custo_total)}
              </Typography>
            </Stack>
          </TableCell>
        </TableRow>
      ))}
      <TableRow sx={{ bgcolor: 'action.selected' }}>
        <TableCell colSpan={4} sx={{ pl: 5 }}>
          <Typography variant="caption" fontWeight={700} color="text.secondary">
            Total da composição
          </Typography>
        </TableCell>
        <TableCell align="right">
          <Typography variant="caption" fontWeight={700}>
            {formatCurrency(totalComposicao)}
          </Typography>
        </TableCell>
      </TableRow>
    </>
  );
}

function ServiceRow({ row }: { row: ServicoTcpoResponse }) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <TableRow
        hover
        sx={{ cursor: 'pointer', '& > td': { borderBottom: open ? 'none' : undefined } }}
        onClick={() => setOpen((v) => !v)}
      >
        <TableCell sx={{ width: 48, p: 0.5, pl: 1 }}>
          <IconButton size="small" aria-label={open ? 'colapsar' : 'expandir'}>
            {open ? <ExpandMoreIcon fontSize="small" /> : <ChevronRightIcon fontSize="small" />}
          </IconButton>
        </TableCell>
        <TableCell>
          <Typography variant="body2" fontFamily="monospace" fontSize={12}>
            {row.codigo_origem}
          </Typography>
        </TableCell>
        <TableCell>
          <Typography variant="body2">{row.descricao}</Typography>
        </TableCell>
        <TableCell>
          <Typography variant="body2">{row.unidade_medida}</Typography>
        </TableCell>
        <TableCell align="right">
          <Typography variant="body2">{formatCurrency(row.custo_unitario ?? row.custo_base)}</Typography>
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell colSpan={5} sx={{ p: 0, border: 'none' }}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Table size="small">
              <TableBody>
                {open && <ComposicaoRow servicoId={row.id} />}
              </TableBody>
            </Table>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
}

export function ServicesPage() {
  const { user, selectedClientId } = useAuth();
  const { showMessage } = useFeedback();
  const queryClient = useQueryClient();
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 25;
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<CreateServiceFormInput, undefined, CreateServiceFormOutput>({
    resolver: zodResolver(createServiceSchema),
    defaultValues: {
      codigo_origem: '',
      descricao: '',
      unidade_medida: '',
      custo_unitario: 0,
      categoria_id: '',
    },
  });

  const servicesQuery = useQuery({
    queryKey: ['services', selectedClientId, query, page, user?.is_admin],
    queryFn: () =>
      servicesApi.list({
        page,
        page_size: PAGE_SIZE,
        q: query || undefined,
        tipo_recurso: 'SERVICO',
        cliente_id: selectedClientId || undefined,
      }),
    enabled: Boolean(user && (selectedClientId || user.is_admin)),
  });

  const createServiceMutation = useMutation({
    mutationFn: (values: CreateServiceFormOutput) =>
      servicesApi.create({
        codigo_origem: values.codigo_origem,
        descricao: values.descricao,
        unidade_medida: values.unidade_medida,
        custo_unitario: values.custo_unitario,
        categoria_id: values.categoria_id ? Number(values.categoria_id) : null,
      }),
    onSuccess: () => {
      showMessage(successMessages.serviceCreated);
      setCreateDialogOpen(false);
      reset();
      void queryClient.invalidateQueries({ queryKey: ['services'] });
    },
  });

  if (!selectedClientId && !user?.is_admin) {
    return (
      <>
        <PageHeader
          title="Catálogo de Serviços"
          description="Serviços disponíveis para orçamentação. Expanda cada linha para ver a composição."
        />
        <EmptyState
          title="Selecione um cliente para listar o catálogo"
          description="Defina o cliente no topo para carregar os serviços visíveis."
        />
      </>
    );
  }

  const items = servicesQuery.data?.items ?? [];
  const total = servicesQuery.data?.total ?? 0;
  const totalPages = servicesQuery.data?.pages ?? 0;

  return (
    <>
      <PageHeader
        title="Catálogo de Serviços"
        description={`${total > 0 ? total.toLocaleString('pt-BR') + ' serviços' : 'Carregando...'} — expanda para ver composição`}
        actions={
          user?.is_admin ? (
            <Button
              variant="contained"
              startIcon={<AddOutlinedIcon />}
              onClick={() => setCreateDialogOpen(true)}
            >
              Novo serviço
            </Button>
          ) : undefined
        }
      />

      <Paper sx={{ p: 2, border: '1px solid', borderColor: 'divider' }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 2 }}>
          <TextField
            fullWidth
            label="Buscar serviço"
            placeholder="Descrição ou código..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(1);
            }}
            size="small"
          />
          {servicesQuery.isLoading && <CircularProgress size={28} sx={{ alignSelf: 'center' }} />}
        </Stack>

        {servicesQuery.isError ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            {extractApiErrorMessage(servicesQuery.error, errorMessages.loadData)}
          </Alert>
        ) : null}

        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ width: 48 }} />
                <TableCell sx={{ width: 180 }}>Código</TableCell>
                <TableCell>Descrição</TableCell>
                <TableCell sx={{ width: 80 }}>Unidade</TableCell>
                <TableCell align="right" sx={{ width: 140 }}>Custo unit. (R$)</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {items.length === 0 && !servicesQuery.isLoading ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 6 }}>
                    <Typography variant="body2" color="text.secondary">
                      Nenhum serviço encontrado.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                items.map((row) => <ServiceRow key={row.id} row={row} />)
              )}
            </TableBody>
          </Table>
        </TableContainer>

        {totalPages > 1 && (
          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary">
              Página {page} de {totalPages} ({total.toLocaleString('pt-BR')} serviços)
            </Typography>
            <Stack direction="row" spacing={1}>
              <Button size="small" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                Anterior
              </Button>
              <Button
                size="small"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Próxima
              </Button>
            </Stack>
          </Stack>
        )}
      </Paper>

      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Novo serviço</DialogTitle>
        <DialogContent dividers>
          <Stack
            component="form"
            spacing={2}
            sx={{ mt: 0.5 }}
            onSubmit={handleSubmit((values) => createServiceMutation.mutate(values))}
          >
            <TextField
              label="Código"
              error={Boolean(errors.codigo_origem)}
              helperText={errors.codigo_origem?.message}
              {...register('codigo_origem')}
            />
            <TextField
              label="Descrição"
              multiline
              minRows={3}
              error={Boolean(errors.descricao)}
              helperText={errors.descricao?.message}
              {...register('descricao')}
            />
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <TextField
                label="Unidade"
                error={Boolean(errors.unidade_medida)}
                helperText={errors.unidade_medida?.message}
                {...register('unidade_medida')}
              />
              <TextField
                label="Custo unitário"
                type="number"
                error={Boolean(errors.custo_unitario)}
                helperText={errors.custo_unitario?.message}
                {...register('custo_unitario', { valueAsNumber: true })}
              />
            </Stack>
            <TextField
              label="Categoria"
              error={Boolean(errors.categoria_id)}
              helperText={errors.categoria_id?.message}
              {...register('categoria_id')}
            />
            {createServiceMutation.isError ? (
              <Alert severity="error">
                {extractApiErrorMessage(createServiceMutation.error, errorMessages.serviceSave)}
              </Alert>
            ) : null}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={handleSubmit((values) => createServiceMutation.mutate(values))}
            disabled={createServiceMutation.isPending}
          >
            {createServiceMutation.isPending ? (
              <CircularProgress size={20} color="inherit" />
            ) : (
              'Salvar'
            )}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

