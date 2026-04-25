import { CssBaseline, ThemeProvider } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type PropsWithChildren, useMemo, useState } from 'react';
import { BrowserRouter } from 'react-router-dom';

import { AuthProvider } from '../features/auth/AuthProvider';
import { FeedbackProvider } from '../shared/components/feedback/FeedbackProvider';
import { ColorModeProvider, useColorMode } from './theme/ColorModeContext';
import { createDinamicaTheme } from './theme/theme';

function ThemedProviders({ children }: PropsWithChildren) {
  const { mode } = useColorMode();
  const theme = useMemo(() => createDinamicaTheme(mode), [mode]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
}

export function AppProviders({ children }: PropsWithChildren) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            refetchOnWindowFocus: false,
            retry: 1,
            staleTime: 30_000,
          },
          mutations: {
            retry: 0,
          },
        },
      }),
  );

  return (
    <ColorModeProvider>
      <ThemedProviders>
        <QueryClientProvider client={queryClient}>
          <FeedbackProvider>
            <BrowserRouter>
              <AuthProvider>{children}</AuthProvider>
            </BrowserRouter>
          </FeedbackProvider>
        </QueryClientProvider>
      </ThemedProviders>
    </ColorModeProvider>
  );
}
