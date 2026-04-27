import ClearOutlinedIcon from '@mui/icons-material/ClearOutlined';
import {
  IconButton,
  MenuItem,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';

interface ClientOption {
  id: string;
  nome: string;
}

interface ClientSelectorProps {
  isAdmin: boolean;
  selectedClientId: string;
  availableClients: ClientOption[];
  onChange: (clienteId: string) => void;
}

export function ClientSelector({
  isAdmin,
  selectedClientId,
  availableClients,
  onChange,
}: ClientSelectorProps) {
  // Admin with no scoped clients: free-form UUID input (can access any client)
  if (isAdmin && !availableClients.length) {
    return (
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        spacing={1}
        alignItems={{ xs: 'stretch', sm: 'center' }}
        sx={{ width: { xs: '100%', md: 'auto' } }}
      >
        <TextField
          size="small"
          label="Cliente"
          fullWidth
          value={selectedClientId}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Cole o UUID do cliente"
          sx={{
            width: { xs: '100%', sm: 260, lg: 340 },
          }}
        />
        <Tooltip title="Limpar contexto de cliente">
          <span>
            <IconButton
              size="small"
              color="inherit"
              onClick={() => onChange('')}
              disabled={!selectedClientId}
            >
              <ClearOutlinedIcon fontSize="small" />
            </IconButton>
          </span>
        </Tooltip>
      </Stack>
    );
  }

  if (!availableClients.length) {
    return (
      <Typography variant="body2" color="text.secondary">
        Sem vínculo de cliente carregado.
      </Typography>
    );
  }

  const availableIds = availableClients.map((c) => c.id);
  const safeValue = availableIds.includes(selectedClientId) ? selectedClientId : '';

  return (
    <TextField
      select
      size="small"
      label="Cliente"
      fullWidth
      value={safeValue}
      onChange={(event) => onChange(event.target.value)}
      sx={{
        width: { xs: '100%', sm: 240, lg: 280 },
      }}
    >
      <MenuItem value="">Selecione</MenuItem>
      {availableClients.map((client) => (
        <MenuItem key={client.id} value={client.id}>
          {client.nome || client.id}
        </MenuItem>
      ))}
    </TextField>
  );
}
