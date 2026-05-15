import ClearOutlinedIcon from '@mui/icons-material/ClearOutlined';
import {
  Autocomplete,
  CircularProgress,
  IconButton,
  MenuItem,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useState } from 'react';

import { clientsApi } from '../../services/api/clientsApi';
import type { ClienteResponse } from '../../types/contracts/clientes';

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
  // Admin with no scoped clients: name-searchable selector querying the API
  if (isAdmin && !availableClients.length) {
    return <AdminClientSearch selectedClientId={selectedClientId} onChange={onChange} />;
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
          {client.nome || 'Cliente sem nome'}
        </MenuItem>
      ))}
    </TextField>
  );
}

function AdminClientSearch({
  selectedClientId,
  onChange,
}: {
  selectedClientId: string;
  onChange: (id: string) => void;
}) {
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState(false);
  // Cache the selected option so the combobox shows the name when closed
  const [cachedOption, setCachedOption] = useState<ClienteResponse | null>(null);

  const { data, isFetching } = useQuery({
    queryKey: ['admin-client-search', search],
    queryFn: () => clientsApi.list({ nome: search || undefined, page: 1, page_size: 20 }),
    enabled: open,
    staleTime: 30_000,
  });

  const options: ClienteResponse[] = data?.items ?? [];
  // Use live option when available; fall back to cache when dropdown is closed
  const selectedOption =
    options.find((c) => c.id === selectedClientId) ??
    (cachedOption?.id === selectedClientId ? cachedOption : null);

  // Stable callback — prevents MUI useAutocomplete from looping on every render
  const handleInputChange = useCallback(
    (_: React.SyntheticEvent, v: string, reason: string) => {
      if (reason === 'input') setSearch(v);
      else if (reason === 'clear') setSearch('');
      // 'reset' (triggered by MUI internally on open/close) is intentionally ignored
    },
    [],
  );

  const handleChange = useCallback(
    (_: React.SyntheticEvent, val: ClienteResponse | null) => {
      if (val) {
        setCachedOption(val);
        onChange(val.id);
      }
    },
    [onChange],
  );

  return (
    <Stack direction="row" spacing={1} alignItems="center" sx={{ width: { xs: '100%', md: 'auto' } }}>
      <Autocomplete<ClienteResponse>
        open={open}
        onOpen={() => setOpen(true)}
        onClose={() => setOpen(false)}
        size="small"
        options={options}
        getOptionLabel={(opt) => (opt ? (opt.nome_fantasia || opt.razao_social || 'Cliente sem nome') : '')}
        isOptionEqualToValue={(opt, val) => opt.id === val.id}
        value={selectedOption}
        // inputValue is intentionally NOT controlled — avoids MUI sync loop (React error #185)
        onInputChange={handleInputChange}
        onChange={handleChange}
        loading={isFetching}
        noOptionsText="Nenhum cliente encontrado"
        sx={{ width: { xs: '100%', sm: 260, lg: 320 } }}
        renderInput={(params) => (
          <TextField
            {...params}
            label="Buscar cliente"
            placeholder="Nome do cliente..."
            InputProps={{
              ...params.InputProps,
              endAdornment: (
                <>
                  {isFetching ? <CircularProgress size={16} /> : null}
                  {params.InputProps.endAdornment}
                </>
              ),
            }}
          />
        )}
      />
      <Tooltip title="Limpar contexto de cliente">
        <span>
          <IconButton
            size="small"
            color="inherit"
            onClick={() => { onChange(''); setSearch(''); setCachedOption(null); }}
            disabled={!selectedClientId}
          >
            <ClearOutlinedIcon fontSize="small" />
          </IconButton>
        </span>
      </Tooltip>
    </Stack>
  );
}

