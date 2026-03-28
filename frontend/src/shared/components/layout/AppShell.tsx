import { Box, Toolbar } from '@mui/material';
import type { PropsWithChildren } from 'react';
import { useState } from 'react';

import { drawerWidth, Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

export function AppShell({ children }: PropsWithChildren) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', backgroundColor: 'background.default' }}>
      <Sidebar
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />

      <Box component="main" sx={{ flex: 1, minWidth: 0 }}>
        <Topbar onMenuClick={() => setMobileOpen(true)} />
        <Toolbar sx={{ minHeight: 72 }} />
        <Box
          sx={{
            px: { xs: 2, md: 3 },
            py: { xs: 2.5, md: 3 },
            maxWidth: { xs: '100%', lg: `calc(100vw - ${drawerWidth}px)` },
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
}
