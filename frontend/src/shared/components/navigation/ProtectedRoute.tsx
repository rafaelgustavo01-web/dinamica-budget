import {
  Alert,
  Box,
  CircularProgress,
} from '@mui/material';
import type { PropsWithChildren, ReactNode } from 'react';
import {
  Navigate,
  useLocation,
} from 'react-router-dom';

import { useAuth } from '../../../features/auth/AuthProvider';
import type { MeResponse } from '../../types/contracts/auth';

function FullScreenLoader() {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        backgroundColor: 'background.default',
      }}
    >
      <CircularProgress color="primary" />
    </Box>
  );
}

export function ProtectedRoute({ children }: PropsWithChildren) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <FullScreenLoader />;
  }

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: `${location.pathname}${location.search}` }}
      />
    );
  }

  return <>{children}</>;
}

export function PublicOnlyRoute({ children }: PropsWithChildren) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <FullScreenLoader />;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}

interface PermissionGuardProps {
  children: ReactNode;
  isAllowed: (user: MeResponse | null) => boolean;
  fallback?: ReactNode;
  redirectTo?: string;
}

export function PermissionGuard({
  children,
  isAllowed,
  fallback,
  redirectTo,
}: PermissionGuardProps) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <FullScreenLoader />;
  }

  if (isAllowed(user)) {
    return <>{children}</>;
  }

  if (redirectTo) {
    return <Navigate to={redirectTo} replace />;
  }

  return (
    <>
      {fallback ?? (
        <Alert severity="warning">
          Você não possui permissão para acessar esta área.
        </Alert>
      )}
    </>
  );
}
