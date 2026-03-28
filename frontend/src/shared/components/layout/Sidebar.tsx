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
import { getNavigationStatusLabel, navigationItems } from './navigationConfig';

export const drawerWidth = 260;

interface SidebarProps {
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function Sidebar({ mobileOpen, onMobileClose }: SidebarProps) {
  const { user } = useAuth();
  const location = useLocation();
  const groups = ['Operação', 'Governança', 'Conta'] as const;

  const content = (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          right: -56,
          top: 92,
          width: 188,
          height: 188,
          borderRadius: 8,
          border: '18px solid rgba(255,255,255,0.05)',
          transform: 'rotate(45deg)',
          pointerEvents: 'none',
        },
      }}
    >
      <Box sx={{ px: 3, py: 3, position: 'relative', zIndex: 1 }}>
        <Stack spacing={1.5}>
          <Stack direction="row" spacing={1.5} alignItems="center">
            <Box
              sx={{
                width: 14,
                height: 42,
                borderRadius: 999,
                backgroundColor: 'secondary.main',
              }}
            />
            <Box>
              <Typography variant="overline" sx={{ color: 'rgba(255,255,255,0.56)' }}>
                Construtora Dinâmica
              </Typography>
              <Typography variant="h5" sx={{ color: 'common.white', lineHeight: 1.1 }}>
                Dinâmica Budget
              </Typography>
            </Box>
          </Stack>
          <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.72)' }}>
            Plataforma operacional para busca, catálogo, homologação e composições.
          </Typography>
        </Stack>
      </Box>

      <Divider sx={{ borderColor: 'rgba(255,255,255,0.08)' }} />

      <Box sx={{ flex: 1, overflowY: 'auto', px: 1.5, py: 2 }}>
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
                  px: 2,
                  textTransform: 'uppercase',
                  color: 'rgba(255,255,255,0.42)',
                  letterSpacing: '0.12em',
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
                      selected={active}
                      sx={{
                        mb: 0.5,
                        borderRadius: 2,
                        borderLeft: active ? '3px solid' : '3px solid transparent',
                        borderLeftColor: active ? 'secondary.main' : 'transparent',
                        color: active ? 'common.white' : 'rgba(255,255,255,0.78)',
                      }}
                    >
                      <ListItemIcon
                        sx={{
                          minWidth: 38,
                          color: active ? 'secondary.main' : 'rgba(255,255,255,0.54)',
                        }}
                      >
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
                            color:
                              item.status === 'partial' ? 'secondary.dark' : 'rgba(255,255,255,0.72)',
                            backgroundColor:
                              item.status === 'partial'
                                ? 'secondary.50'
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
        spacing={0.4}
        sx={{
          px: 3,
          py: 2.5,
          borderTop: '1px solid rgba(255,255,255,0.08)',
          color: 'rgba(255,255,255,0.72)',
        }}
      >
        <Typography variant="body2">Ambiente interno</Typography>
        <Typography variant="caption">
          Navegação adaptada às permissões do usuário autenticado.
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
