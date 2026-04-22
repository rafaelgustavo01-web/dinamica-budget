import {
  Box,
  CircularProgress,
} from '@mui/material';
import { lazy, Suspense } from 'react';
import { Navigate, Outlet, Route, Routes } from 'react-router-dom';

import { AppShell } from '../shared/components/layout/AppShell';
import {
  PermissionGuard,
  ProtectedRoute,
  PublicOnlyRoute,
} from '../shared/components/navigation/ProtectedRoute';
import { hasAdminPanelAccess } from '../shared/utils/permissions';

const AdminPage = lazy(() =>
  import('../features/admin/AdminPage').then((module) => ({
    default: module.AdminPage,
  })),
);
const UploadTcpoPage = lazy(() =>
  import('../features/admin/UploadTcpoPage').then((module) => ({
    default: module.UploadTcpoPage,
  })),
);
const AssociationsPage = lazy(() =>
  import('../features/associations/AssociationsPage').then((module) => ({
    default: module.AssociationsPage,
  })),
);
const LoginPage = lazy(() =>
  import('../features/auth/LoginPage').then((module) => ({
    default: module.LoginPage,
  })),
);
const ClientsPage = lazy(() =>
  import('../features/clients/ClientsPage').then((module) => ({
    default: module.ClientsPage,
  })),
);
const CompositionsPage = lazy(() =>
  import('../features/compositions/CompositionsPage').then((module) => ({
    default: module.CompositionsPage,
  })),
);
const DashboardPage = lazy(() =>
  import('../features/dashboard/DashboardPage').then((module) => ({
    default: module.DashboardPage,
  })),
);
const HomologationPage = lazy(() =>
  import('../features/homologation/HomologationPage').then((module) => ({
    default: module.HomologationPage,
  })),
);
const PermissionsPage = lazy(() =>
  import('../features/permissions/PermissionsPage').then((module) => ({
    default: module.PermissionsPage,
  })),
);
const ProfilePage = lazy(() =>
  import('../features/profile/ProfilePage').then((module) => ({
    default: module.ProfilePage,
  })),
);
const ReportsPage = lazy(() =>
  import('../features/reports/ReportsPage').then((module) => ({
    default: module.ReportsPage,
  })),
);
const SearchPage = lazy(() =>
  import('../features/search/SearchPage').then((module) => ({
    default: module.SearchPage,
  })),
);
const ServicesPage = lazy(() =>
  import('../features/services/ServicesPage').then((module) => ({
    default: module.ServicesPage,
  })),
);
const ExtractionPage = lazy(() =>
  import('../features/extraction/ExtractionPage').then((module) => ({
    default: module.ExtractionPage,
  })),
);
const UsersPage = lazy(() =>
  import('../features/users/UsersPage').then((module) => ({
    default: module.UsersPage,
  })),
);
const PcTabelasPage = lazy(() =>
  import('../features/pc-tabelas/PcTabelasPage').then((module) => ({
    default: module.PcTabelasPage,
  })),
);

function RouteFallback() {
  return (
    <Box
      sx={{
        minHeight: '40vh',
        display: 'grid',
        placeItems: 'center',
      }}
    >
      <CircularProgress color="primary" />
    </Box>
  );
}

function AuthenticatedApp() {
  return (
    <ProtectedRoute>
      <AppShell>
        <Outlet />
      </AppShell>
    </ProtectedRoute>
  );
}

function AdminOnlyLayout() {
  return (
    <PermissionGuard
      isAllowed={(user) => hasAdminPanelAccess(user)}
      redirectTo="/dashboard"
    >
      <Outlet />
    </PermissionGuard>
  );
}

export function AppRouter() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route
          path="/login"
          element={
            <PublicOnlyRoute>
              <LoginPage />
            </PublicOnlyRoute>
          }
        />

        <Route element={<AuthenticatedApp />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/busca" element={<SearchPage />} />
          <Route path="/servicos" element={<ServicesPage />} />
          <Route path="/homologacao" element={<HomologationPage />} />
          <Route path="/composicoes" element={<CompositionsPage />} />
          <Route path="/associacoes" element={<AssociationsPage />} />
          <Route path="/relatorios" element={<ReportsPage />} />
<<<<<<< HEAD
          <Route path="/extracao" element={<ExtractionPage />} />
=======
          <Route path="/pc-tabelas" element={<PcTabelasPage />} />
>>>>>>> 5f0973541797732f99516ee792729f7f3cef10c2
          <Route path="/perfil" element={<ProfilePage />} />

          <Route element={<AdminOnlyLayout />}>
            <Route path="/admin" element={<AdminPage />} />
            <Route path="/upload" element={<UploadTcpoPage />} />
            <Route path="/governanca/upload-tcpo" element={<Navigate to="/upload" replace />} />
            <Route path="/usuarios" element={<UsersPage />} />
            <Route path="/clientes" element={<ClientsPage />} />
            <Route path="/permissoes" element={<PermissionsPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Suspense>
  );
}
