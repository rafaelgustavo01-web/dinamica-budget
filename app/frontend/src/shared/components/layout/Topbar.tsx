import DarkModeOutlinedIcon from '@mui/icons-material/DarkModeOutlined';
import LightModeOutlinedIcon from '@mui/icons-material/LightModeOutlined';
import LogoutOutlinedIcon from '@mui/icons-material/LogoutOutlined';
import MenuOutlinedIcon from '@mui/icons-material/MenuOutlined';
import {
  AppBar,
  Avatar,
  Chip,
  IconButton,
  Stack,
  Toolbar,
  Tooltip,
  Typography,
} from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';

import { useColorMode } from '../../../app/theme/ColorModeContext';
import { useAuth } from '../../../features/auth/AuthProvider';
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
  const { user, logout, selectedClientId, setSelectedClientId, availableClientIds } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const currentTitle = getRouteTitle(location.pathname);
  const currentStatus = getRouteStatus(location.pathname);

  return (
    <AppBar
      position="sticky"
      color="inherit"
      sx={{
        top: 0,
        zIndex: (theme) => theme.zIndex.appBar,
        backdropFilter: 'blur(14px)',
      }}
    >
      <Toolbar
        sx={{
          minHeight: { xs: 88, sm: 96 },
          px: { xs: 2, sm: 3, lg: 4 },
          py: { xs: 1.25, sm: 1.5 },
          gap: 2,
          alignItems: 'center',
          flexWrap: { xs: 'wrap', md: 'nowrap' },
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

        <Stack
          spacing={0.75}
          sx={{
            minWidth: 0,
            flex: '1 1 320px',
            order: { xs: 1, md: 0 },
          }}
        >
          <Stack direction="row" spacing={1} alignItems="center" useFlexGap flexWrap="wrap">
            <Typography variant="overline" sx={{ lineHeight: 1, color: 'text.secondary' }}>
              Workspace
            </Typography>
            <Typography variant="subtitle1" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
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

          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              maxWidth: 720,
              minWidth: 0,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {selectedClientId
              ? `Cliente em contexto: ${shortenUuid(selectedClientId)}`
              : 'Sem cliente selecionado. Escolha um cliente quando o fluxo exigir escopo operacional.'}
          </Typography>
        </Stack>

        <Stack
          direction="row"
          spacing={1.25}
          alignItems="center"
          useFlexGap
          flexWrap="wrap"
          sx={{
            width: { xs: '100%', md: 'auto' },
            justifyContent: { xs: 'space-between', md: 'flex-end' },
            order: { xs: 2, md: 0 },
          }}
        >
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
