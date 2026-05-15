import { AppErrorBoundary } from '../shared/components/errors/AppErrorBoundary';
import { AppProviders } from './providers';
import { AppRouter } from './router';

export function App() {
  return (
    <AppProviders>
      <AppErrorBoundary>
        <AppRouter />
      </AppErrorBoundary>
    </AppProviders>
  );
}
