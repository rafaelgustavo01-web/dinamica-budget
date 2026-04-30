import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, type RenderOptions } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { FeedbackProvider } from '../shared/components/feedback/FeedbackProvider';
import type { ReactElement, ReactNode } from 'react';

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: Infinity, staleTime: Infinity },
      mutations: { retry: false },
    },
  });
}

export function renderWithProviders(
  ui: ReactElement,
  options?: RenderOptions & {
    route?: string;
    initialEntries?: string[];
    path?: string;
  },
) {
  const queryClient = createTestQueryClient();
  const { route, initialEntries, path, ...renderOptions } = options ?? {};

  function Wrapper({ children }: { children: ReactNode }) {
    const content = path ? (
      <Routes>
        <Route path={path} element={children} />
      </Routes>
    ) : (
      children
    );

    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={initialEntries ?? (route ? [route] : ['/'])}>
          <FeedbackProvider>{content}</FeedbackProvider>
        </MemoryRouter>
      </QueryClientProvider>
    );
  }

  return render(ui, { wrapper: Wrapper, ...renderOptions });
}
