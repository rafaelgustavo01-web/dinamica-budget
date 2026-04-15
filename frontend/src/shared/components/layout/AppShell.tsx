import { Box } from '@mui/material';
import type { PropsWithChildren } from 'react';
import { useState } from 'react';

import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

export function AppShell({ children }: PropsWithChildren) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <Box
      sx={{
        display: 'flex',
        minHeight: '100vh',
        backgroundColor: 'background.default',
        overflowX: 'clip',
      }}
    >
      <Sidebar
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />

      <Box
        component="main"
        sx={{
          flex: 1,
          minWidth: 0,
          width: '100%',
          position: 'relative',
          overflowX: 'clip',
        }}
      >
        <Topbar onMenuClick={() => setMobileOpen(true)} />
        <Box
          sx={{
            px: { xs: 2, sm: 3, lg: 4 },
            py: { xs: 2.5, md: 3.5 },
            width: '100%',
          }}
        >
          <Box
            sx={{
              width: '100%',
              maxWidth: 1480,
              mx: 'auto',
              minWidth: 0,
              overflowX: 'clip',
            }}
          >
            {children}
          </Box>
        </Box>
      </Box>
    </Box>
  );
}
