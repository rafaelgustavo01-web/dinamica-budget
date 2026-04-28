import { useState } from 'react';
import {
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { histogramaApi } from '../../../shared/services/api/histogramaApi';

interface Props {
  open: boolean;
  onClose: () => void;
  propostaId: string;
  composicaoId: string;
  composicaoDescricao: string;
}

export function AlocacaoRecursoDialog({ open, onClose, propostaId, composicaoId, composicaoDescricao }: Props) {
  const queryClient = useQueryClient();
  const [recursoExtraId, setRecursoExtraId] = useState('');
  const [quantidadeConsumo, setQuantidadeConsumo] = useState('');

  const { data: extras, isLoading } = useQuery({
    queryKey: ['recursos-extras', propostaId],
    queryFn: () => histogramaApi.listarRecursosExtras(propostaId),
    enabled: open,
  });

  const alocarMutation = useMutation({
    mutationFn: () =>
      histogramaApi.alocarRecurso(propostaId, composicaoId, {
        recurso_extra_id: recursoExtraId,
        quantidade_consumo: parseFloat(quantidadeConsumo.replace(',', '.')),
      }),
    onSuccess: () => {
      setRecursoExtraId('');
      setQuantidadeConsumo('');
      onClose();
      void queryClient.invalidateQueries({ queryKey: ['cpu-itens'] });
      void queryClient.invalidateQueries({ queryKey: ['recursos-extras', propostaId] });
    },
  });

  const handleSubmit = () => {
    if (!recursoExtraId || !quantidadeConsumo) return;
    alocarMutation.mutate();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Alocar Recurso Extra</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Composição: <strong>{composicaoDescricao}</strong>
          </Typography>

          {isLoading && <Typography variant="body2">Carregando recursos...</Typography>}

          {!isLoading && (!extras || extras.length === 0) && (
            <Typography variant="body2" color="warning.main">
              Nenhum recurso extra cadastrado. Adicione recursos na aba "Recursos Extras" do histograma.
            </Typography>
          )}

          {extras && extras.length > 0 && (
            <>
              <FormControl fullWidth required>
                <InputLabel>Recurso Extra</InputLabel>
                <Select
                  value={recursoExtraId}
                  label="Recurso Extra"
                  onChange={(e) => setRecursoExtraId(e.target.value)}
                >
                  {extras.map((extra) => (
                    <MenuItem key={extra.id} value={extra.id}>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <span>{extra.descricao}</span>
                        <Chip label={extra.tipo_recurso} size="small" variant="outlined" />
                        <span style={{ color: 'gray', fontSize: '0.8rem' }}>
                          R$ {extra.custo_unitario.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                        </span>
                      </Stack>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <TextField
                label="Quantidade de Consumo"
                type="number"
                value={quantidadeConsumo}
                onChange={(e) => setQuantidadeConsumo(e.target.value)}
                fullWidth
                required
                helperText="Quantidade deste recurso consumida nesta composição"
              />
            </>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancelar</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={!recursoExtraId || !quantidadeConsumo || alocarMutation.isPending}
        >
          Alocar
        </Button>
      </DialogActions>
    </Dialog>
  );
}
