import { createTheme } from '@mui/material';

export const appTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#0f4c5c',
      dark: '#0b3742',
      light: '#3c7280',
    },
    secondary: {
      main: '#c57b57',
      dark: '#9e6144',
      light: '#d39a7f',
    },
    background: {
      default: '#f3f5f7',
      paper: '#ffffff',
    },
    success: {
      main: '#2f7d4b',
    },
    warning: {
      main: '#b86a00',
    },
    error: {
      main: '#b42318',
    },
    text: {
      primary: '#0f1720',
      secondary: '#475467',
    },
    divider: '#d0d5dd',
  },
  typography: {
    fontFamily: '"IBM Plex Sans", "Segoe UI", sans-serif',
    h1: {
      fontSize: '2.6rem',
      fontWeight: 700,
      letterSpacing: '-0.03em',
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 700,
      letterSpacing: '-0.02em',
    },
    h3: {
      fontSize: '1.5rem',
      fontWeight: 600,
    },
    h4: {
      fontSize: '1.125rem',
      fontWeight: 600,
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 14,
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backdropFilter: 'blur(16px)',
          backgroundImage: 'none',
          boxShadow: 'none',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: '1px solid #d0d5dd',
          backgroundColor: '#0f1720',
          color: '#ffffff',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          border: '1px solid #e4e7ec',
        },
      },
    },
    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
        },
      },
    },
  },
});
