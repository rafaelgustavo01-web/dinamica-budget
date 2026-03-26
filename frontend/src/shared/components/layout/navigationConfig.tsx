import AdminPanelSettingsOutlinedIcon from '@mui/icons-material/AdminPanelSettingsOutlined';
import AssignmentTurnedInOutlinedIcon from '@mui/icons-material/AssignmentTurnedInOutlined';
import DatasetLinkedOutlinedIcon from '@mui/icons-material/DatasetLinkedOutlined';
import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined';
import GroupOutlinedIcon from '@mui/icons-material/GroupOutlined';
import HubOutlinedIcon from '@mui/icons-material/HubOutlined';
import ManageAccountsOutlinedIcon from '@mui/icons-material/ManageAccountsOutlined';
import PersonOutlineOutlinedIcon from '@mui/icons-material/PersonOutlineOutlined';
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined';
import SourceOutlinedIcon from '@mui/icons-material/SourceOutlined';
import SpaceDashboardOutlinedIcon from '@mui/icons-material/SpaceDashboardOutlined';
import StorefrontOutlinedIcon from '@mui/icons-material/StorefrontOutlined';
import type { ReactNode } from 'react';

import type { MeResponse } from '../../types/contracts/auth';

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
    label: 'Busca Inteligente',
    path: '/busca',
    group: 'Operação',
    icon: <SearchOutlinedIcon fontSize="small" />,
    status: 'active',
    visible: () => true,
  },
  {
    label: 'Serviços',
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
    status: 'partial',
    statusLabel: 'Somente visualização',
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
    status: 'partial',
    visible: () => true,
  },
  {
    label: 'Administração',
    path: '/admin',
    group: 'Governança',
    icon: <AdminPanelSettingsOutlinedIcon fontSize="small" />,
    status: 'active',
    visible: (user) => Boolean(user?.is_admin),
  },
  {
    label: 'Usuários',
    path: '/usuarios',
    group: 'Governança',
    icon: <GroupOutlinedIcon fontSize="small" />,
    status: 'active',
    visible: (user) => Boolean(user?.is_admin),
  },
  {
    label: 'Clientes',
    path: '/clientes',
    group: 'Governança',
    icon: <StorefrontOutlinedIcon fontSize="small" />,
    status: 'partial',
    visible: (user) => Boolean(user?.is_admin),
  },
  {
    label: 'Permissões',
    path: '/permissoes',
    group: 'Governança',
    icon: <ManageAccountsOutlinedIcon fontSize="small" />,
    status: 'missing',
    showInMenu: false,
    visible: (user) => Boolean(user?.is_admin),
  },
  {
    label: 'Meu Perfil',
    path: '/perfil',
    group: 'Conta',
    icon: <PersonOutlineOutlinedIcon fontSize="small" />,
    status: 'partial',
    visible: () => true,
  },
];

export function getRouteTitle(pathname: string) {
  const currentItem =
    navigationItems.find((item) => pathname === item.path) ??
    navigationItems.find((item) => pathname.startsWith(`${item.path}/`));

  return currentItem?.label ?? 'Dinamica Budget';
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
