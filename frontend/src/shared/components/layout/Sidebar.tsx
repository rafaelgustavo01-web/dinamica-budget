import {
  Box,
  Chip,
  Divider,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Typography,
} from '@mui/material';
import { NavLink, useLocation } from 'react-router-dom';

import { useAuth } from '../../../features/auth/AuthProvider';
import {
  getNavigationStatusLabel,
  navigationItems,
} from './navigationConfig';

export const drawerWidth = 288;

interface SidebarProps {
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function Sidebar({ mobileOpen, onMobileClose }: SidebarProps) {
  const { user } = useAuth();
  const location = useLocation();
  const groups = ['Operação', 'Governança', 'Conta'] as const;

  const content = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ px: 3, py: 3 }}>
        <Typography variant="overline" sx={{ color: 'rgba(255,255,255,0.68)' }}>
          Dinamica Budget
        </Typography>
        <Typography variant="h5" sx={{ color: 'common.white', mt: 0.5 }}>
          Operação orçamentária
        </Typography>
        <Typography variant="body2" sx={{ mt: 1, color: 'rgba(255,255,255,0.72)' }}>
          Frontend oficial alinhado ao backend FastAPI e ao RBAC por cliente.
        </Typography>
      </Box>

      <Divider sx={{ borderColor: 'rgba(255,255,255,0.08)' }} />

      <Box sx={{ flex: 1, overflowY: 'auto', px: 2, py: 2 }}>
        {groups.map((group) => {
          const items = navigationItems.filter(
            (item) => item.group === group && item.visible(user) && item.showInMenu !== false,
          );

          if (!items.length) {
            return null;
          }

          return (
            <Box key={group} sx={{ mb: 2.5 }}>
              <Typography
                variant="caption"
                sx={{
                  px: 1.5,
                  textTransform: 'uppercase',
                  color: 'rgba(255,255,255,0.42)',
                  letterSpacing: '0.08em',
                }}
              >
                {group}
              </Typography>

              <List sx={{ mt: 1, py: 0 }}>
                {items.map((item) => {
                  const active =
                    location.pathname === item.path ||
                    location.pathname.startsWith(`${item.path}/`);

                  return (
                    <ListItemButton
                      key={item.path}
                      component={NavLink}
                      to={item.path}
                      onClick={onMobileClose}
                      sx={{
                        borderRadius: 2.5,
                        mb: 0.5,
                        color: active ? '#ffffff' : 'rgba(255,255,255,0.82)',
                        backgroundColor: active
                          ? 'rgba(197,123,87,0.22)'
                          : 'transparent',
                        '&:hover': {
                          backgroundColor: active
                            ? 'rgba(197,123,87,0.26)'
                            : 'rgba(255,255,255,0.06)',
                        },
                      }}
                    >
                      <ListItemIcon sx={{ color: 'inherit', minWidth: 36 }}>
                        {item.icon}
                      </ListItemIcon>
                      <ListItemText
                        primary={item.label}
                        primaryTypographyProps={{ fontSize: 14, fontWeight: 500 }}
                      />
                      {item.status !== 'active' ? (
                        <Chip
                          size="small"
                          label={getNavigationStatusLabel(item)}
                          sx={{
                            ml: 1,
                            color: '#ffffff',
                            backgroundColor:
                              item.status === 'partial'
                                ? 'rgba(197,123,87,0.26)'
                                : 'rgba(255,255,255,0.12)',
                          }}
                        />
                      ) : null}
                    </ListItemButton>
                  );
                })}
              </List>
            </Box>
          );
        })}
      </Box>

      <Stack
        spacing={0.5}
        sx={{
          px: 3,
          py: 2.5,
          borderTop: '1px solid rgba(255,255,255,0.08)',
          color: 'rgba(255,255,255,0.72)',
        }}
      >
        <Typography variant="body2">Ambiente interno</Typography>
        <Typography variant="caption">
          O menu principal exibe apenas módulos operacionais ou parciais com backend utilizável.
        </Typography>
      </Stack>
    </Box>
  );

  return (
    <>
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={onMobileClose}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', lg: 'none' },
          '& .MuiDrawer-paper': { width: drawerWidth },
        }}
      >
        {content}
      </Drawer>

      <Drawer
        variant="permanent"
        open
        sx={{
          display: { xs: 'none', lg: 'block' },
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        {content}
      </Drawer>
    </>
  );
}
