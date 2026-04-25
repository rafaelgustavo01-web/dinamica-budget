import {
  Alert,
  AlertTitle,
  List,
  ListItem,
  ListItemText,
  Paper,
  Stack,
  Typography,
} from '@mui/material';

interface ContractNoticeProps {
  title: string;
  description: string;
  missingContracts: string[];
  availableNow?: string[];
}

export function ContractNotice({
  title,
  description,
  missingContracts,
  availableNow,
}: ContractNoticeProps) {
  return (
    <Paper
      sx={{
        p: 3,
        border: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Stack spacing={2}>
        <Alert severity="warning" variant="standard">
          <AlertTitle>{title}</AlertTitle>
          {description}
        </Alert>

        {availableNow?.length ? (
          <div>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              Disponível agora
            </Typography>
            <List dense sx={{ py: 0 }}>
              {availableNow.map((item) => (
                <ListItem key={item} sx={{ px: 0 }}>
                  <ListItemText primary={item} />
                </ListItem>
              ))}
            </List>
          </div>
        ) : null}

        <div>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Contratos ainda pendentes
          </Typography>
          <List dense sx={{ py: 0 }}>
            {missingContracts.map((contract) => (
              <ListItem key={contract} sx={{ px: 0 }}>
                <ListItemText primary={contract} />
              </ListItem>
            ))}
          </List>
        </div>
      </Stack>
    </Paper>
  );
}
