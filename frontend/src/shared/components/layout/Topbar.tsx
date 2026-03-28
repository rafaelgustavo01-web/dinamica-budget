import DarkModeOutlinedIcon from '@mui/icons-material/DarkModeOutlined';
import LightModeOutlinedIcon from '@mui/icons-material/LightModeOutlined';
import LogoutOutlinedIcon from '@mui/icons-material/LogoutOutlined';
import MenuOutlinedIcon from '@mui/icons-material/MenuOutlined';
import {
  AppBar,
  Avatar,
  Box,
  Chip,
  IconButton,
  Stack,
  Toolbar,
  Tooltip,
  Typography,
} from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../../../features/auth/AuthProvider';
import { useColorMode } from '../../../app/theme/ColorModeContext';
import { shortenUuid } from '../../utils/format';
import { ClientSelector } from './ClientSelector';
import { getRouteStatus, getRouteTitle, getStatusLabel } from './navigationConfig';

interface TopbarProps {
  onMenuClick: () => void;
}

function getInitials(name: string | undefined, fallback: string) {
  if (!name) {
    return fallback.slice(0, 2).toUpperCase();
  }

  const initials = name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('');

  return initials.toUpperCase();
}

export function Topbar({ onMenuClick }: TopbarProps) {
  const { mode, toggleColorMode } = useColorMode();
  const {
    user,
    logout,
    selectedClientId,
    setSelectedClientId,
    availableClientIds,
  } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const currentTitle = getRouteTitle(location.pathname);
  const currentStatus = getRouteStatus(location.pathname);

  return (
    <AppBar
      position="fixed"
      color="inherit"
      sx={{
        width: { lg: 'calc(100% - 260px)' },
        ml: { lg: '260px' },
      }}
    >
      <Toolbar
        sx={{
          minHeight: 72,
          px: { xs: 2, md: 3 },
          gap: 2,
          alignItems: 'center',
        }}
      >
        <IconButton
          color="inherit"
          edge="start"
          onClick={onMenuClick}
          sx={{ display: { lg: 'none' } }}
        >
          <MenuOutlinedIcon />
        </IconButton>

        <Stack direction="row" spacing={1.5} alignItems="center" sx={{ minWidth: 0 }}>
          <Box
            sx={{
              width: 12,
              height: 36,
              borderRadius: 999,
              backgroundColor: 'secondary.main',
              flexShrink: 0,
            }}
          />
          <Box sx={{ minWidth: 0 }}>
            <Typography
              variant="overline"
              sx={{ display: 'block', lineHeight: 1.1, color: 'text.secondary' }}
            >
              Construtora Dinâmica
            </Typography>
            <Stack
              direction="row"
              spacing={1}
              alignItems="center"
              useFlexGap
              flexWrap="wrap"
            >
              <Typography variant="h5" sx={{ lineHeight: 1.15 }}>
                {currentTitle}
              </Typography>
              {currentStatus !== 'active' ? (
                <Chip
                  size="small"
                  label={getStatusLabel(currentStatus)}
                  sx={
                    currentStatus === 'partial'
                      ? {
                          color: 'secondary.dark',
                          backgroundColor: 'secondary.50',
                        }
                      : undefined
                  }
                />
              ) : null}
            </Stack>
            <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 680 }}>
              {selectedClientId
                ? `Cliente em contexto: ${shortenUuid(selectedClientId)}`
                : 'Selecione um cliente quando o fluxo exigir escopo operacional.'}
            </Typography>
          </Box>
        </Stack>

        <Box sx={{ flex: 1 }} />

        <Stack direction="row" spacing={1.5} alignItems="center">
          <ClientSelector
            isAdmin={Boolean(user?.is_admin)}
            selectedClientId={selectedClientId}
            availableClientIds={availableClientIds}
            onChange={setSelectedClientId}
          />

          <Tooltip title={mode === 'light' ? 'Ativar modo escuro' : 'Ativar modo claro'}>
            <IconButton color="inherit" onClick={toggleColorMode}>
              {mode === 'light' ? <DarkModeOutlinedIcon /> : <LightModeOutlinedIcon />}
            </IconButton>
          </Tooltip>

          {user ? (
            <Tooltip title="Meu perfil">
              <IconButton color="inherit" onClick={() => navigate('/perfil')}>
                <Avatar
                  sx={{
                    width: 36,
                    height: 36,
                    bgcolor: 'primary.main',
                    color: 'primary.contrastText',
                    fontSize: 13,
                    fontWeight: 700,
                  }}
                >
                  {getInitials(user.nome, user.email)}
                </Avatar>
              </IconButton>
            </Tooltip>
          ) : null}

          <Tooltip title="Sair">
            <IconButton color="inherit" onClick={() => void logout()}>
              <LogoutOutlinedIcon />
            </IconButton>
          </Tooltip>
        </Stack>
      </Toolbar>
    </AppBar>
  );
}
