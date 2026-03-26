import ClearOutlinedIcon from '@mui/icons-material/ClearOutlined';
import {
  IconButton,
  MenuItem,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';

interface ClientSelectorProps {
  isAdmin: boolean;
  selectedClientId: string;
  availableClientIds: string[];
  onChange: (clienteId: string) => void;
}

export function ClientSelector({
  isAdmin,
  selectedClientId,
  availableClientIds,
  onChange,
}: ClientSelectorProps) {
  if (isAdmin) {
    return (
      <Stack direction="row" spacing={1} alignItems="center">
        <TextField
          size="small"
          label="Cliente (UUID)"
          value={selectedClientId}
          onChange={(event) => onChange(event.target.value)}
          placeholder="Cole o UUID quando a rota exigir cliente"
          sx={{ minWidth: 280 }}
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

  if (!availableClientIds.length) {
    return (
      <Typography variant="body2" color="text.secondary">
        Sem vínculo de cliente carregado.
      </Typography>
    );
  }

  return (
    <TextField
      select
      size="small"
      label="Cliente"
      value={selectedClientId}
      onChange={(event) => onChange(event.target.value)}
      sx={{ minWidth: 240 }}
    >
      {availableClientIds.map((clienteId) => (
        <MenuItem key={clienteId} value={clienteId}>
          {clienteId}
        </MenuItem>
      ))}
    </TextField>
  );
}
