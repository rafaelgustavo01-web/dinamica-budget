import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Typography,
  Box,
} from '@mui/material';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { proposalsApi, type PropostaPapel } from '../../../shared/services/api/proposalsApi';
import { extractApiErrorMessage } from '../../../shared/services/api/apiClient';

interface ProposalShareDialogProps {
  propostaId: string;
  open: boolean;
  onClose: () => void;
}

const PAPEL_LABELS: Record<PropostaPapel, string> = {
  OWNER: 'Proprietário',
  EDITOR: 'Editor',
  APROVADOR: 'Aprovador',
};

export function ProposalShareDialog({ propostaId, open, onClose }: ProposalShareDialogProps) {
  const queryClient = useQueryClient();
  const [newUserId, setNewUserId] = useState('');
  const [newPapel, setNewPapel] = useState<PropostaPapel>('EDITOR');

  const { data: acl = [], isLoading, error } = useQuery({
    queryKey: ['proposta-acl', propostaId],
    queryFn: () => proposalsApi.listAcl(propostaId),
    enabled: open,
  });

  const addMutation = useMutation({
    mutationFn: () => proposalsApi.addAcl(propostaId, { usuario_id: newUserId, papel: newPapel }),
    onSuccess: () => {
      setNewUserId('');
      void queryClient.invalidateQueries({ queryKey: ['proposta-acl', propostaId] });
    },
  });

  const removeMutation = useMutation({
    mutationFn: ({ usuarioId, papel }: { usuarioId: string; papel: PropostaPapel }) =>
      proposalsApi.removeAcl(propostaId, usuarioId, papel),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['proposta-acl', propostaId] });
    },
  });

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Compartilhar Proposta</DialogTitle>
      <DialogContent>
        {(error || addMutation.isError || removeMutation.isError) && (
          <Typography color="error" variant="body2" sx={{ mb: 2 }}>
            {extractApiErrorMessage(error ?? addMutation.error ?? removeMutation.error)}
          </Typography>
        )}

        <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center' }}>
          <FormControl sx={{ flex: 2 }}>
            <InputLabel>ID do Usuário</InputLabel>
            <Select value={newUserId} label="ID do Usuário" onChange={(e) => setNewUserId(e.target.value)}>
              {/* Em produção, buscar lista de usuários do sistema */}
              <MenuItem value=""><em>Selecione...</em></MenuItem>
              <MenuItem value="user-editor-1">Usuário Editor</MenuItem>
              <MenuItem value="user-aprover-1">Usuário Aprovador</MenuItem>
            </Select>
          </FormControl>
          <FormControl sx={{ flex: 1 }}>
            <InputLabel>Papel</InputLabel>
            <Select value={newPapel} label="Papel" onChange={(e) => setNewPapel(e.target.value as PropostaPapel)}>
              <MenuItem value="EDITOR">Editor</MenuItem>
              <MenuItem value="APROVADOR">Aprovador</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="contained"
            onClick={() => addMutation.mutate()}
            disabled={!newUserId || addMutation.isPending}
          >
            Adicionar
          </Button>
        </Box>

        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Nome</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Papel</TableCell>
                <TableCell align="right">Ação</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {isLoading ? (
                <TableRow><TableCell colSpan={4}>Carregando...</TableCell></TableRow>
              ) : acl.length === 0 ? (
                <TableRow><TableCell colSpan={4}>Nenhum compartilhamento.</TableCell></TableRow>
              ) : (
                acl.map((item) => (
                  <TableRow key={`${item.usuario_id}-${item.papel}`}>
                    <TableCell>{item.usuario_nome}</TableCell>
                    <TableCell>{item.usuario_email}</TableCell>
                    <TableCell>{PAPEL_LABELS[item.papel]}</TableCell>
                    <TableCell align="right">
                      <Button
                        size="small"
                        color="error"
                        startIcon={<DeleteOutlineIcon />}
                        onClick={() => removeMutation.mutate({ usuarioId: item.usuario_id, papel: item.papel })}
                        disabled={removeMutation.isPending}
                      >
                        Remover
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Fechar</Button>
      </DialogActions>
    </Dialog>
  );
}
