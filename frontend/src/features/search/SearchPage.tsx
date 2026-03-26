import {
  Alert,
  Box,
  Button,
  Divider,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { useState } from 'react';
import { z } from 'zod';

import { useAuth } from '../auth/AuthProvider';
import { ConfirmationDialog } from '../../shared/components/ConfirmationDialog';
import { DataTable } from '../../shared/components/DataTable';
import { EmptyState } from '../../shared/components/EmptyState';
import { PageHeader } from '../../shared/components/PageHeader';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { useFeedback } from '../../shared/components/feedback/FeedbackProvider';
import { extractApiErrorMessage } from '../../shared/services/api/apiClient';
import { searchApi } from '../../shared/services/api/searchApi';
import { servicesApi } from '../../shared/services/api/servicesApi';
import type {
  BuscaServicoResponse,
  ResultadoBusca,
} from '../../shared/types/contracts/busca';
import { formatCurrency, formatNumber } from '../../shared/utils/format';

const searchSchema = z.object({
  texto_busca: z.string().min(2, 'Use pelo menos 2 caracteres.').max(500),
  limite_resultados: z.coerce.number().min(1).max(50),
  threshold_score: z.coerce.number().min(0).max(1),
});

type SearchFormInput = z.input<typeof searchSchema>;
type SearchFormOutput = z.output<typeof searchSchema>;

export function SearchPage() {
  const { selectedClientId } = useAuth();
  const { showMessage } = useFeedback();
  const [searchResponse, setSearchResponse] = useState<BuscaServicoResponse | null>(null);
  const [selectedResult, setSelectedResult] = useState<ResultadoBusca | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SearchFormInput, undefined, SearchFormOutput>({
    resolver: zodResolver(searchSchema),
    defaultValues: {
      texto_busca: '',
      limite_resultados: 5,
      threshold_score: 0.65,
    },
  });

  const searchMutation = useMutation({
    mutationFn: (values: SearchFormOutput) =>
      searchApi.buscar({
        cliente_id: selectedClientId,
        ...values,
      }),
    onSuccess: (data) => {
      setSearchResponse(data);
      setSelectedResult(data.resultados[0] ?? null);
      showMessage(`${data.resultados.length} resultado(s) carregado(s).`);
    },
  });

  const compositionQuery = useQuery({
    queryKey: ['search', 'composition', selectedResult?.id_tcpo],
    queryFn: () => servicesApi.getComposicao(selectedResult!.id_tcpo),
    enabled: Boolean(selectedResult?.id_tcpo),
  });

  const associateMutation = useMutation({
    mutationFn: () =>
      searchApi.associar({
        cliente_id: selectedClientId,
        texto_busca_original: searchResponse?.texto_buscado ?? '',
        id_tcpo_selecionado: selectedResult?.id_tcpo ?? '',
        id_historico_busca: searchResponse?.metadados.id_historico_busca ?? '',
      }),
    onSuccess: (data) => {
      showMessage(data.mensagem);
      setConfirmOpen(false);
    },
  });

  if (!selectedClientId) {
    return (
      <>
        <PageHeader
          title="Busca Inteligente"
          description="Fluxo principal de correspondência, associação e rastreabilidade."
        />
        <EmptyState
          title="Selecione um cliente antes da busca"
          description="O contrato oficial de busca exige `cliente_id`. Defina o contexto no topo para consultar o backend."
        />
      </>
    );
  }

  return (
    <>
      <PageHeader
        title="Busca Inteligente"
        description="Consulta em cascata com item próprio, associação direta, fuzzy e IA semântica, seguida de associação manual confirmada pelo usuário."
      />

      <Stack direction={{ xs: 'column', xl: 'row' }} spacing={2} alignItems="stretch">
        <Paper sx={{ flex: 1.05, p: 3 }}>
          <Stack
            component="form"
            spacing={2}
            onSubmit={handleSubmit((values) => searchMutation.mutate(values))}
          >
            <TextField
              label="Descrição do serviço"
              placeholder="Ex.: escavação manual de valas"
              error={Boolean(errors.texto_busca)}
              helperText={errors.texto_busca?.message}
              {...register('texto_busca')}
            />

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <TextField
                label="Limite de resultados"
                type="number"
                error={Boolean(errors.limite_resultados)}
                helperText={errors.limite_resultados?.message}
                {...register('limite_resultados', { valueAsNumber: true })}
              />
              <TextField
                label="Threshold"
                type="number"
                inputProps={{ step: '0.01', min: '0', max: '1' }}
                error={Boolean(errors.threshold_score)}
                helperText={errors.threshold_score?.message}
                {...register('threshold_score', { valueAsNumber: true })}
              />
            </Stack>

            <Button variant="contained" type="submit" disabled={searchMutation.isPending}>
              Buscar
            </Button>
          </Stack>

          {searchMutation.isError ? (
            <Alert severity="error" sx={{ mt: 2 }}>
              {extractApiErrorMessage(
                searchMutation.error,
                'Falha ao executar a busca.',
              )}
            </Alert>
          ) : null}

          {searchResponse ? (
            <Box sx={{ mt: 3 }}>
              <Stack
                direction={{ xs: 'column', md: 'row' }}
                justifyContent="space-between"
                spacing={1}
                sx={{ mb: 1.5 }}
              >
                <Typography variant="h6">Resultados</Typography>
                <Typography variant="body2" color="text.secondary">
                  Histórico: {searchResponse.metadados.id_historico_busca ?? '-'} | Tempo:{' '}
                  {searchResponse.metadados.tempo_processamento_ms ?? 0} ms
                </Typography>
              </Stack>

              <DataTable
                columns={[
                  { key: 'codigo', header: 'Código', render: (row) => row.codigo_origem },
                  { key: 'descricao', header: 'Descrição', render: (row) => row.descricao },
                  {
                    key: 'origem',
                    header: 'Origem do match',
                    render: (row) => (
                      <StatusBadge kind="origemMatch" value={row.origem_match} />
                    ),
                  },
                  {
                    key: 'score',
                    header: 'Confiança',
                    align: 'right',
                    render: (row) => formatNumber(row.score_confianca),
                  },
                  {
                    key: 'custo',
                    header: 'Custo',
                    align: 'right',
                    render: (row) => formatCurrency(row.custo_unitario),
                  },
                ]}
                rows={searchResponse.resultados}
                rowKey={(row) => row.id_tcpo}
                page={1}
                pageSize={Math.max(searchResponse.resultados.length, 1)}
                total={searchResponse.resultados.length}
                emptyTitle="Nenhum resultado encontrado"
                emptyDescription="O backend não retornou correspondências para o texto e cliente informados."
                onRowClick={(row) => setSelectedResult(row)}
              />
            </Box>
          ) : null}
        </Paper>

        <Paper sx={{ flex: 0.95, p: 3 }}>
          <Typography variant="h6" sx={{ mb: 1.5 }}>
            Item selecionado
          </Typography>
          {selectedResult ? (
            <Stack spacing={1.5}>
              <Typography variant="subtitle1">{selectedResult.descricao}</Typography>
              <Typography variant="body2" color="text.secondary">
                Código: {selectedResult.codigo_origem}
              </Typography>
              <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                <StatusBadge kind="origemMatch" value={selectedResult.origem_match} />
                <StatusBadge value={selectedResult.status_homologacao} />
              </Stack>
              <Typography variant="body2" color="text.secondary">
                Score: {formatNumber(selectedResult.score_confianca)} | Custo:{' '}
                {formatCurrency(selectedResult.custo_unitario)}
              </Typography>

              <Divider />

              <Typography variant="subtitle2">Composição expandida</Typography>
              {compositionQuery.isFetching ? (
                <Typography variant="body2" color="text.secondary">
                  Carregando composição...
                </Typography>
              ) : compositionQuery.data ? (
                <>
                  <Typography variant="body2" color="text.secondary">
                    Total: {formatCurrency(compositionQuery.data.custo_total_composicao)}
                  </Typography>
                  <Stack spacing={1}>
                    {compositionQuery.data.itens.length ? (
                      compositionQuery.data.itens.map((item) => (
                        <Paper key={item.id} variant="outlined" sx={{ p: 1.5 }}>
                          <Typography variant="body2">{item.descricao_filho}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {formatNumber(item.quantidade_consumo)} {item.unidade_medida} ·{' '}
                            {formatCurrency(item.custo_total)}
                          </Typography>
                        </Paper>
                      ))
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        O item não possui composição cadastrada.
                      </Typography>
                    )}
                  </Stack>
                </>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Selecione um resultado para abrir os dados expandidos.
                </Typography>
              )}

              <Button variant="contained" onClick={() => setConfirmOpen(true)}>
                Confirmar vínculo
              </Button>
            </Stack>
          ) : (
            <Typography variant="body2" color="text.secondary">
              Execute uma busca e escolha um item da lista para revisar a composição e confirmar o vínculo.
            </Typography>
          )}
        </Paper>
      </Stack>

      <ConfirmationDialog
        open={confirmOpen}
        title="Confirmar associação"
        confirmLabel="Confirmar vínculo"
        isLoading={associateMutation.isPending}
        onCancel={() => setConfirmOpen(false)}
        onConfirm={() => associateMutation.mutate()}
      >
        <Stack spacing={1}>
          <Typography variant="body2">
            Texto buscado: {searchResponse?.texto_buscado}
          </Typography>
          <Typography variant="body2">
            Serviço selecionado: {selectedResult?.descricao}
          </Typography>
          {associateMutation.isError ? (
            <Alert severity="error">
              {extractApiErrorMessage(
                associateMutation.error,
                'Falha ao confirmar a associação.',
              )}
            </Alert>
          ) : null}
        </Stack>
      </ConfirmationDialog>
    </>
  );
}
