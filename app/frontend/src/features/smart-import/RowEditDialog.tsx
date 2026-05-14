import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
} from '@mui/material';
import { useEffect, useState } from 'react';

import type { RowPatch, StagingRow } from '../../shared/services/api/smartImportApi';

interface Props {
  open: boolean;
  row: StagingRow | null;
  onClose: () => void;
  onSave: (patch: RowPatch) => void;
  loading?: boolean;
}

export function RowEditDialog({ open, row, onClose, onSave, loading = false }: Props) {
  const [fields, setFields] = useState<RowPatch>({});

  useEffect(() => {
    if (row) {
      setFields({
        codigo: row.codigo ?? '',
        descricao: row.descricao ?? '',
        unidade: row.unidade ?? '',
        quantidade: row.quantidade ?? '',
        preco: row.preco ?? '',
        valor: row.valor ?? '',
      });
    }
  }, [row]);

  const set = (key: keyof RowPatch) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setFields((prev) => ({ ...prev, [key]: e.target.value }));

  const handleSave = () => {
    const patch: RowPatch = {};
    for (const [k, v] of Object.entries(fields)) {
      if (v !== undefined) patch[k as keyof RowPatch] = v === '' ? null : v;
    }
    onSave(patch);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Editar Linha</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          <TextField label="Código" value={fields.codigo ?? ''} onChange={set('codigo')} size="small" />
          <TextField
            label="Descrição"
            value={fields.descricao ?? ''}
            onChange={set('descricao')}
            size="small"
            required
          />
          <TextField label="Unidade" value={fields.unidade ?? ''} onChange={set('unidade')} size="small" />
          <TextField label="Quantidade" value={fields.quantidade ?? ''} onChange={set('quantidade')} size="small" />
          <TextField label="Preço" value={fields.preco ?? ''} onChange={set('preco')} size="small" />
          <TextField label="Valor" value={fields.valor ?? ''} onChange={set('valor')} size="small" />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancelar
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={loading || !fields.descricao}
        >
          Salvar
        </Button>
      </DialogActions>
    </Dialog>
  );
}
