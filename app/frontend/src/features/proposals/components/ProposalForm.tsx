import { zodResolver } from '@hookform/resolvers/zod';
import { Button, Stack, TextField } from '@mui/material';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import type { PropostaFormData } from '../types';

const schema = z.object({
  titulo: z.string().min(3, 'O título deve ter pelo menos 3 caracteres.'),
  descricao: z.string().optional(),
});

interface ProposalFormProps {
  onSubmit: (data: PropostaFormData) => void;
  isLoading: boolean;
  onCancel: () => void;
}

export function ProposalForm({ onSubmit, isLoading, onCancel }: ProposalFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PropostaFormData>({
    resolver: zodResolver(schema),
  });

  return (
    <Stack component="form" spacing={3} onSubmit={handleSubmit(onSubmit)} sx={{ maxWidth: 600 }}>
      <TextField
        label="Título da Proposta"
        error={!!errors.titulo}
        helperText={errors.titulo?.message}
        fullWidth
        {...register('titulo')}
      />

      <TextField
        label="Descrição"
        multiline
        rows={4}
        fullWidth
        {...register('descricao')}
      />

      <Stack direction="row" spacing={2} justifyContent="flex-end">
        <Button variant="outlined" onClick={onCancel} disabled={isLoading}>
          Cancelar
        </Button>
        <Button variant="contained" type="submit" disabled={isLoading}>
          {isLoading ? 'Criando...' : 'Criar Proposta'}
        </Button>
      </Stack>
    </Stack>
  );
}
