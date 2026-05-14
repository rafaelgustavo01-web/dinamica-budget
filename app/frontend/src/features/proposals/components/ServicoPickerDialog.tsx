import { useState, useEffect } from 'react';
import {
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  List,
  ListItemButton,
  ListItemText,
  TextField,
  Typography,
} from '@mui/material';
import { useMutation } from '@tanstack/react-query';
import { searchApi } from '../../../shared/services/api/searchApi';
import { formatCurrency, getOrigemMatchLabel } from '../../../shared/utils/format';
import type { ResultadoBusca } from '../../../shared/types/contracts/busca';
import type { TipoServicoMatch } from '../../../shared/services/api/proposalsApi';

interface ServicoPickerDialogProps {
  open: boolean;
  clienteId: string;
  descricaoOriginal: string;
  onSelect: (servicoId: string, tipo: TipoServicoMatch) => void;
  onClose: () => void;
}

export function ServicoPickerDialog({
  open,
  clienteId,
  descricaoOriginal,
  onSelect,
  onClose,
}: ServicoPickerDialogProps) {
  const [texto, setTexto] = useState(descricaoOriginal);

  const buscaMutation = useMutation({
    mutationFn: () =>
      searchApi.buscar({
        cliente_id: clienteId,
        texto_busca: texto,
        limite_resultados: 10,
        threshold_score: 0.5,
      }),
  });

  // Auto-trigger search when dialog opens
  useEffect(() => {
    if (open) {
      setTexto(descricaoOriginal);
      setTimeout(() => buscaMutation.mutate(), 0);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  function handleSelect(resultado: ResultadoBusca) {
    const tipo: TipoServicoMatch =
      resultado.origem_match === 'PROPRIA_CLIENTE' ? 'ITEM_PROPRIO' : 'BASE_TCPO';
    onSelect(resultado.id_tcpo, tipo);
    onClose();
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Substituir Serviço</DialogTitle>
      <DialogContent>
        <TextField
          fullWidth
          label="Buscar serviço"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          sx={{ mt: 1, mb: 2 }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') buscaMutation.mutate();
          }}
        />
        <Button
          variant="outlined"
          onClick={() => buscaMutation.mutate()}
          disabled={buscaMutation.isPending || !texto.trim()}
        >
          {buscaMutation.isPending ? <CircularProgress size={18} /> : 'Buscar'}
        </Button>

        {buscaMutation.isSuccess && buscaMutation.data.resultados.length === 0 && (
          <Typography sx={{ mt: 2 }} color="text.secondary">
            Nenhum resultado encontrado.
          </Typography>
        )}

        {buscaMutation.isSuccess && buscaMutation.data.resultados.length > 0 && (
          <List sx={{ mt: 1 }}>
            {buscaMutation.data.resultados.map((r, idx) => {
              const scoreNum = r.score_confianca;
              const scoreColor: 'success' | 'warning' | 'error' =
                scoreNum >= 0.85 ? 'success' : scoreNum >= 0.65 ? 'warning' : 'error';
              const origemLabel = getOrigemMatchLabel(r.origem_match as Parameters<typeof getOrigemMatchLabel>[0]);
              return (
                <ListItemButton
                  key={r.id_tcpo}
                  onClick={() => handleSelect(r)}
                  sx={idx === 0 ? { borderLeft: '3px solid', borderColor: 'primary.main', pl: 1.25 } : {}}
                >
                  <ListItemText
                    primary={r.descricao}
                    secondary={
                      <>
                        {r.codigo_origem} · {r.unidade} · {formatCurrency(r.custo_unitario)}{' '}
                        <Chip label={`${(scoreNum * 100).toFixed(0)}%`} color={scoreColor} size="small" sx={{ ml: 0.5, height: 18, fontSize: '0.7rem' }} />
                        {' '}
                        <Chip label={origemLabel} size="small" variant="outlined" sx={{ height: 18, fontSize: '0.7rem' }} />
                      </>
                    }
                  />
                </ListItemButton>
              );
            })}
          </List>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancelar</Button>
      </DialogActions>
    </Dialog>
  );
}
