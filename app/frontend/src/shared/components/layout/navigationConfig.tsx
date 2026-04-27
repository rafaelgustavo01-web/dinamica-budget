import AdminPanelSettingsOutlinedIcon from '@mui/icons-material/AdminPanelSettingsOutlined';
import AssignmentTurnedInOutlinedIcon from '@mui/icons-material/AssignmentTurnedInOutlined';
import DatasetLinkedOutlinedIcon from '@mui/icons-material/DatasetLinkedOutlined';
import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined';
import TableViewOutlinedIcon from '@mui/icons-material/TableViewOutlined';
import GroupOutlinedIcon from '@mui/icons-material/GroupOutlined';
import HubOutlinedIcon from '@mui/icons-material/HubOutlined';
import ManageAccountsOutlinedIcon from '@mui/icons-material/ManageAccountsOutlined';
import PersonOutlineOutlinedIcon from '@mui/icons-material/PersonOutlineOutlined';
import PublishOutlinedIcon from '@mui/icons-material/PublishOutlined';
import ReceiptLongOutlinedIcon from '@mui/icons-material/ReceiptLongOutlined';
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined';
import SourceOutlinedIcon from '@mui/icons-material/SourceOutlined';
import SpaceDashboardOutlinedIcon from '@mui/icons-material/SpaceDashboardOutlined';
import StorefrontOutlinedIcon from '@mui/icons-material/StorefrontOutlined';
import TableChartOutlinedIcon from '@mui/icons-material/TableChartOutlined';
import type { ReactNode } from 'react';

import type { MeResponse } from '../../types/contracts/auth';
import { hasAdminPanelAccess } from '../../utils/permissions';

export type NavigationStatus = 'active' | 'partial' | 'missing';

export interface NavigationItem {
  label: string;
  path: string;
  group: 'Operação' | 'Governança' | 'Conta';
  icon: ReactNode;
  status: NavigationStatus;
  visible: (user: MeResponse | null) => boolean;
  showInMenu?: boolean;
  statusLabel?: string;
}

export const navigationItems: NavigationItem[] = [
  {
    label: 'Dashboard',
    path: '/dashboard',
    group: 'Operação',
    icon: <SpaceDashboardOutlinedIcon fontSize="small" />,
    status: 'active',
    visible: () => true,
  },
  {
    label: 'Orçamentos',
    path: '/propostas',
    group: 'Operação',
    icon: <ReceiptLongOutlinedIcon fontSize="small" />,
    status: 'active',
    visible: () => true,
  },
  {
    label: 'Busca Inteligente',
    path: '/busca',
    group: 'Operação',
    icon: <SearchOutlinedIcon fontSize="small" />,
    status: 'active',
    visible: () => true,
  },
  {
    label: 'Catálogo de Serviços',
    path: '/servicos',
    group: 'Operação',
    icon: <SourceOutlinedIcon fontSize="small" />,
    status: 'active',
    visible: () => true,
  },
  {
    label: 'Composições',
    path: '/composicoes',
    group: 'Operação',
    icon: <HubOutlinedIcon fontSize="small" />,
    status: 'active',
    visible: () => true,
  },
  {
    label: 'Associações',
    path: '/associacoes',
    group: 'Operação',
    icon: <DatasetLinkedOutlinedIcon fontSize="small" />,
    status: 'active',
    visible: () => true,
  },
  {
    label: 'Homologação',
    path: '/homologacao',
    group: 'Operação',
    icon: <AssignmentTurnedInOutlinedIcon fontSize="small" />,
    status: 'active',
    visible: () => true,
  },
  {
    label: 'Relatórios',
    path: '/relatorios',
    group: 'Operação',
    icon: <DescriptionOutlinedIcon fontSize="small" />,
    status: 'active',
    visible: () => true,
  },
  {
    label: 'Extração PC',
    path: '/extracao',
    group: 'Operação',
    icon: <TableViewOutlinedIcon fontSize="small" />,
    status: 'active',
    visible: () => true,
  },
  {
    label: 'Administração',
    path: '/admin',
    group: 'Governança',
    icon: <AdminPanelSettingsOutlinedIcon fontSize="small" />,
    status: 'active',
    visible: (user) => hasAdminPanelAccess(user),
  },
  {
    label: 'BCU',
    path: '/bcu',
    group: 'Operação',
    icon: <TableChartOutlinedIcon fontSize="small" />,
    status: 'active',
    visible: () => true,
  },
  {
    label: 'De/Para BCU',
    path: '/bcu/de-para',
    group: 'Operação',
    icon: <DatasetLinkedOutlinedIcon fontSize="small" />,
    status: 'active',
    visible: (user) => hasAdminPanelAccess(user),
  },
  {
    label: 'Upload',
    path: '/upload',
    group: 'Governança',
    icon: <PublishOutlinedIcon fontSize="small" />,
    status: 'active',
    visible: (user) => hasAdminPanelAccess(user),
  },
  {
    label: 'Usuários',
    path: '/usuarios',
    group: 'Governança',
    icon: <GroupOutlinedIcon fontSize="small" />,
    status: 'active',
    visible: (user) => hasAdminPanelAccess(user),
  },
  {
    label: 'Clientes',
    path: '/clientes',
    group: 'Governança',
    icon: <StorefrontOutlinedIcon fontSize="small" />,
    status: 'active',
    visible: (user) => hasAdminPanelAccess(user),
  },
  {
    label: 'Permissões',
    path: '/permissoes',
    group: 'Governança',
    icon: <ManageAccountsOutlinedIcon fontSize="small" />,
    status: 'missing',
    showInMenu: false,
    visible: (user) => hasAdminPanelAccess(user),
  },
  {
    label: 'Meu Perfil',
    path: '/perfil',
    group: 'Conta',
    icon: <PersonOutlineOutlinedIcon fontSize="small" />,
    status: 'active',
    visible: () => true,
  },
];

export function getRouteTitle(pathname: string) {
  const currentItem =
    navigationItems.find((item) => pathname === item.path) ??
    navigationItems.find((item) => pathname.startsWith(`${item.path}/`));

  return currentItem?.label ?? 'Dinâmica Budget';
}

export function getRouteStatus(pathname: string) {
  const currentItem =
    navigationItems.find((item) => pathname === item.path) ??
    navigationItems.find((item) => pathname.startsWith(`${item.path}/`));

  return currentItem?.status ?? 'active';
}

export function getStatusLabel(status: NavigationStatus) {
  const labels: Record<NavigationStatus, string> = {
    active: 'Ativo',
    partial: 'Parcial',
    missing: 'Contrato pendente',
  };

  return labels[status];
}

export function getNavigationStatusLabel(item: NavigationItem) {
  return item.statusLabel ?? getStatusLabel(item.status);
}
