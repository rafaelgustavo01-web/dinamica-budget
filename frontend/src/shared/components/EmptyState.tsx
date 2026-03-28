import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { Box, Button, Paper, Stack, Typography } from '@mui/material';
import type { ReactNode } from 'react';

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: ReactNode;
}

export function EmptyState({
  title,
  description,
  actionLabel,
  onAction,
  icon,
}: EmptyStateProps) {
  return (
    <Paper
      variant="outlined"
      sx={{
        p: { xs: 4, md: 5 },
        borderColor: 'divider',
        backgroundColor: 'background.paper',
      }}
    >
      <Stack spacing={2} alignItems="center" textAlign="center">
        <Box
          sx={{
            width: 72,
            height: 72,
            borderRadius: '50%',
            display: 'grid',
            placeItems: 'center',
            backgroundColor: 'action.hover',
            color: 'primary.main',
          }}
        >
          {icon ?? <InfoOutlinedIcon sx={{ fontSize: 34 }} />}
        </Box>
        <Typography variant="h5">{title}</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 560 }}>
          {description}
        </Typography>
        {actionLabel && onAction ? (
          <Button variant="outlined" color="primary" onClick={onAction}>
            {actionLabel}
          </Button>
        ) : null}
      </Stack>
    </Paper>
  );
}
