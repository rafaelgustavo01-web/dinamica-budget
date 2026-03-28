import { Box, Stack, Typography } from '@mui/material';
import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  description: string;
  actions?: ReactNode;
}

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <Stack
      direction={{ xs: 'column', lg: 'row' }}
      spacing={2}
      justifyContent="space-between"
      alignItems={{ xs: 'flex-start', lg: 'flex-end' }}
      sx={{ mb: 3 }}
    >
      <Box
        sx={{
          position: 'relative',
          pl: 2.5,
          maxWidth: 780,
          '&::before': {
            content: '""',
            position: 'absolute',
            left: 0,
            top: 8,
            bottom: 8,
            width: 4,
            borderRadius: 999,
            background:
              'linear-gradient(180deg, var(--db-secondary) 0%, rgba(240,192,92,1) 100%)',
          },
        }}
      >
        <Typography variant="h2" sx={{ mb: 0.8 }}>
          {title}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {description}
        </Typography>
      </Box>

      {actions ? <Box sx={{ width: { xs: '100%', lg: 'auto' } }}>{actions}</Box> : null}
    </Stack>
  );
}
