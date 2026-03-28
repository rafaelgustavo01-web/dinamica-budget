import { createTheme, type PaletteMode, type ThemeOptions } from '@mui/material/styles';

import {
  chartColors,
  customShadows,
  darkTokens,
  fonts,
  statusColors,
  tokens,
} from './tokens';

const typography: ThemeOptions['typography'] = {
  fontFamily: fonts.primary,
  h1: {
    fontFamily: fonts.display,
    fontSize: '2rem',
    fontWeight: 700,
    lineHeight: 1.2,
    letterSpacing: '-0.5px',
  },
  h2: {
    fontFamily: fonts.display,
    fontSize: '1.625rem',
    fontWeight: 700,
    lineHeight: 1.25,
    letterSpacing: '-0.3px',
  },
  h3: {
    fontFamily: fonts.display,
    fontSize: '1.375rem',
    fontWeight: 600,
    lineHeight: 1.3,
    letterSpacing: '-0.2px',
  },
  h4: {
    fontFamily: fonts.primary,
    fontSize: '1.25rem',
    fontWeight: 600,
    lineHeight: 1.35,
    letterSpacing: '-0.1px',
  },
  h5: {
    fontFamily: fonts.primary,
    fontSize: '1.125rem',
    fontWeight: 600,
    lineHeight: 1.4,
  },
  h6: {
    fontFamily: fonts.primary,
    fontSize: '1rem',
    fontWeight: 600,
    lineHeight: 1.4,
    letterSpacing: '0.15px',
  },
  subtitle1: {
    fontFamily: fonts.primary,
    fontSize: '1rem',
    fontWeight: 500,
    lineHeight: 1.5,
    letterSpacing: '0.15px',
  },
  subtitle2: {
    fontFamily: fonts.primary,
    fontSize: '0.875rem',
    fontWeight: 500,
    lineHeight: 1.5,
    letterSpacing: '0.1px',
  },
  body1: {
    fontFamily: fonts.primary,
    fontSize: '0.9375rem',
    fontWeight: 400,
    lineHeight: 1.6,
  },
  body2: {
    fontFamily: fonts.primary,
    fontSize: '0.8125rem',
    fontWeight: 400,
    lineHeight: 1.55,
    letterSpacing: '0.1px',
  },
  caption: {
    fontFamily: fonts.primary,
    fontSize: '0.75rem',
    fontWeight: 400,
    lineHeight: 1.5,
    letterSpacing: '0.4px',
  },
  overline: {
    fontFamily: fonts.primary,
    fontSize: '0.6875rem',
    fontWeight: 600,
    lineHeight: 1.5,
    letterSpacing: '1.5px',
    textTransform: 'uppercase',
  },
  button: {
    fontFamily: fonts.primary,
    fontSize: '0.875rem',
    fontWeight: 600,
    lineHeight: 1.15,
    letterSpacing: '0.4px',
    textTransform: 'uppercase',
  },
};

const getComponentOverrides = (mode: PaletteMode): ThemeOptions['components'] => {
  const isLight = mode === 'light';
  const surfaceBorder = isLight ? tokens.neutral[200] : darkTokens.border.default;
  const surfaceBase = isLight ? '#FFFFFF' : darkTokens.bg.paper;

  return {
    MuiCssBaseline: {
      styleOverrides: {
        ':root': {
          '--db-primary': isLight ? tokens.primary.main : darkTokens.primary.main,
          '--db-primary-dark': isLight ? tokens.primary[800] : darkTokens.primary.dark,
          '--db-primary-soft': isLight ? tokens.primary[50] : 'rgba(90,138,208,0.12)',
          '--db-secondary': isLight ? tokens.secondary.main : darkTokens.secondary.main,
          '--db-secondary-dark': isLight ? tokens.secondary.dark : darkTokens.secondary.dark,
          '--db-bg-default': isLight ? tokens.neutral[50] : darkTokens.bg.default,
          '--db-bg-paper': isLight ? '#FFFFFF' : darkTokens.bg.paper,
          '--db-bg-subtle': isLight ? tokens.neutral[100] : darkTokens.bg.alt,
          '--db-border': surfaceBorder,
          '--db-border-input': isLight ? tokens.neutral[400] : darkTokens.border.input,
          '--db-text-primary': isLight ? tokens.neutral[800] : darkTokens.text.primary,
          '--db-text-secondary': isLight ? tokens.neutral[600] : darkTokens.text.secondary,
          '--db-text-disabled': isLight ? tokens.neutral[500] : darkTokens.text.disabled,
          '--db-scrollbar-track': isLight ? 'rgba(27,42,74,0.04)' : 'rgba(255,255,255,0.04)',
          '--db-scrollbar-thumb-start': isLight
            ? 'rgba(27,58,107,0.45)'
            : 'rgba(90,138,208,0.55)',
          '--db-scrollbar-thumb-end': isLight
            ? 'rgba(27,42,74,0.65)'
            : 'rgba(27,58,107,0.75)',
        },
        '*, *::before, *::after': {
          boxSizing: 'border-box',
        },
        html: {
          colorScheme: mode,
        },
        body: {
          fontVariantNumeric: 'tabular-nums lining-nums',
          background: isLight
            ? `radial-gradient(circle at top right, rgba(232,166,35,0.14), transparent 20%),
               radial-gradient(circle at bottom left, rgba(27,58,107,0.08), transparent 28%),
               linear-gradient(180deg, ${tokens.neutral[50]} 0%, ${tokens.neutral[100]} 100%)`
            : `radial-gradient(circle at top right, rgba(240,185,66,0.12), transparent 18%),
               radial-gradient(circle at bottom left, rgba(90,138,208,0.14), transparent 30%),
               linear-gradient(180deg, ${darkTokens.bg.default} 0%, #121A29 100%)`,
          color: isLight ? tokens.neutral[800] : darkTokens.text.primary,
          transition: 'background-color 180ms ease, color 180ms ease',
        },
        '::selection': {
          backgroundColor: isLight ? tokens.primary[100] : 'rgba(90,138,208,0.24)',
          color: isLight ? tokens.primary[800] : darkTokens.text.primary,
        },
      },
    },
    MuiAppBar: {
      defaultProps: {
        elevation: 0,
        color: 'default',
      },
      styleOverrides: {
        root: {
          backgroundColor: surfaceBase,
          backgroundImage: 'none',
          borderBottom: `1px solid ${surfaceBorder}`,
          color: isLight ? tokens.neutral[800] : darkTokens.text.primary,
          boxShadow: 'none',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: isLight ? tokens.primary[800] : '#0A101A',
          color: '#FFFFFF',
          borderRight: isLight ? 'none' : '1px solid #1A2640',
          width: 260,
          backgroundImage:
            'linear-gradient(180deg, rgba(255,255,255,0.025), rgba(255,255,255,0) 28%)',
        },
      },
    },
    MuiPaper: {
      defaultProps: {
        elevation: 0,
      },
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
        rounded: {
          borderRadius: 8,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          border: `1px solid ${surfaceBorder}`,
          backgroundColor: surfaceBase,
          boxShadow: customShadows[1],
        },
      },
    },
    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
      styleOverrides: {
        root: {
          borderRadius: 6,
          padding: '8px 20px',
          minHeight: 40,
          transition: 'all 150ms ease-in-out',
        },
        containedPrimary: {
          '&:hover': {
            backgroundColor: isLight ? tokens.primary[800] : darkTokens.primary.dark,
          },
        },
        containedSecondary: {
          color: tokens.primary[800],
          '&:hover': {
            backgroundColor: '#C48A1A',
          },
        },
        outlined: {
          borderWidth: 1,
          '&:hover': {
            borderWidth: 1,
          },
        },
        text: {
          '&:hover': {
            backgroundColor: isLight ? 'rgba(27,58,107,0.04)' : 'rgba(90,138,208,0.12)',
          },
        },
        sizeSmall: {
          padding: '6px 14px',
          minHeight: 34,
        },
        sizeLarge: {
          padding: '10px 28px',
          minHeight: 48,
        },
      },
    },
    MuiTextField: {
      defaultProps: {
        variant: 'outlined',
        size: 'medium',
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          backgroundColor: surfaceBase,
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: isLight ? tokens.neutral[500] : darkTokens.border.input,
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: isLight ? tokens.primary.main : darkTokens.primary.main,
            borderWidth: 2,
            boxShadow: isLight
              ? '0 0 0 3px rgba(27,58,107,0.12)'
              : '0 0 0 3px rgba(90,138,208,0.16)',
          },
        },
        notchedOutline: {
          borderColor: isLight ? tokens.neutral[400] : darkTokens.border.input,
        },
        input: {
          padding: '12px 14px',
        },
      },
    },
    MuiInputLabel: {
      styleOverrides: {
        root: {
          color: isLight ? tokens.neutral[600] : darkTokens.text.secondary,
          '&.Mui-focused': {
            color: isLight ? tokens.primary.main : darkTokens.primary.main,
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          fontWeight: 600,
          fontSize: '0.75rem',
          letterSpacing: '0.5px',
          textTransform: 'uppercase',
          height: 24,
        },
        sizeSmall: {
          height: 20,
          fontSize: '0.6875rem',
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 12,
          boxShadow: customShadows[12],
        },
      },
    },
    MuiDialogTitle: {
      styleOverrides: {
        root: {
          fontFamily: fonts.display,
          fontSize: '1.25rem',
          fontWeight: 600,
          padding: '24px 32px 16px',
        },
      },
    },
    MuiDialogContent: {
      styleOverrides: {
        root: {
          padding: '16px 32px',
        },
      },
    },
    MuiDialogActions: {
      styleOverrides: {
        root: {
          padding: '16px 32px 24px',
          gap: 12,
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          '& .MuiTableCell-head': {
            backgroundColor: isLight ? tokens.primary[800] : darkTokens.bg.alt,
            color: '#FFFFFF',
            fontWeight: 600,
            fontSize: '0.8125rem',
            letterSpacing: '0.5px',
            textTransform: 'uppercase',
            padding: '12px 16px',
            borderBottom: 'none',
            whiteSpace: 'nowrap',
          },
        },
      },
    },
    MuiTableBody: {
      styleOverrides: {
        root: {
          '& .MuiTableRow-root': {
            '&:nth-of-type(even)': {
              backgroundColor: isLight ? tokens.neutral[50] : 'rgba(255,255,255,0.02)',
            },
            '&:hover': {
              backgroundColor: isLight ? tokens.primary[50] : 'rgba(255,255,255,0.05)',
            },
            transition: 'background-color 100ms ease',
          },
          '& .MuiTableCell-body': {
            padding: '12px 16px',
            fontSize: '0.875rem',
            borderColor: surfaceBorder,
            fontVariantNumeric: 'tabular-nums lining-nums',
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderColor: surfaceBorder,
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '14px 16px',
          fontSize: '0.875rem',
          alignItems: 'center',
        },
        standardSuccess: {
          backgroundColor: isLight ? tokens.success.light : darkTokens.success.light,
          color: isLight ? tokens.success.dark : darkTokens.success.main,
          borderLeft: `4px solid ${isLight ? tokens.success.main : darkTokens.success.main}`,
          '& .MuiAlert-icon': {
            color: isLight ? tokens.success.main : darkTokens.success.main,
          },
        },
        standardWarning: {
          backgroundColor: isLight ? tokens.warning.light : darkTokens.warning.light,
          color: isLight ? tokens.warning.dark : darkTokens.warning.main,
          borderLeft: `4px solid ${isLight ? tokens.warning.main : darkTokens.warning.main}`,
          '& .MuiAlert-icon': {
            color: isLight ? tokens.warning.main : darkTokens.warning.main,
          },
        },
        standardError: {
          backgroundColor: isLight ? tokens.error.light : darkTokens.error.light,
          color: isLight ? tokens.error.dark : darkTokens.error.main,
          borderLeft: `4px solid ${isLight ? tokens.error.main : darkTokens.error.main}`,
          '& .MuiAlert-icon': {
            color: isLight ? tokens.error.main : darkTokens.error.main,
          },
        },
        standardInfo: {
          backgroundColor: isLight ? tokens.info.light : darkTokens.info.light,
          color: isLight ? tokens.info.dark : darkTokens.info.main,
          borderLeft: `4px solid ${isLight ? tokens.info.main : darkTokens.info.main}`,
          '& .MuiAlert-icon': {
            color: isLight ? tokens.info.main : darkTokens.info.main,
          },
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: isLight ? tokens.primary[800] : '#10192A',
          color: '#FFFFFF',
          fontSize: '0.75rem',
          fontWeight: 500,
          borderRadius: 6,
          padding: '6px 12px',
        },
        arrow: {
          color: isLight ? tokens.primary[800] : '#10192A',
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          fontWeight: 600,
          fontSize: '0.875rem',
          letterSpacing: '0.3px',
          textTransform: 'uppercase',
          minHeight: 48,
          '&.Mui-selected': {
            color: isLight ? tokens.primary.main : darkTokens.primary.main,
          },
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        indicator: {
          height: 3,
          borderRadius: '3px 3px 0 0',
          backgroundColor: isLight ? tokens.primary.main : darkTokens.primary.main,
        },
      },
    },
    MuiBadge: {
      styleOverrides: {
        colorError: {
          backgroundColor: tokens.error.main,
          color: '#FFFFFF',
          fontWeight: 600,
          fontSize: '0.6875rem',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          margin: '2px 8px',
          padding: '10px 12px',
          '&.Mui-selected': {
            backgroundColor: isLight ? 'rgba(232,166,35,0.15)' : 'rgba(240,185,66,0.15)',
            borderLeft: `3px solid ${isLight ? tokens.secondary.main : darkTokens.secondary.main}`,
            '&:hover': {
              backgroundColor: isLight ? 'rgba(232,166,35,0.22)' : 'rgba(240,185,66,0.22)',
            },
          },
          '&:hover': {
            backgroundColor: 'rgba(255,255,255,0.08)',
          },
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          height: 6,
          backgroundColor: isLight ? tokens.neutral[200] : darkTokens.border.default,
        },
      },
    },
    MuiSkeleton: {
      styleOverrides: {
        root: {
          borderRadius: 6,
        },
      },
    },
    MuiBreadcrumbs: {
      styleOverrides: {
        root: {
          fontSize: '0.8125rem',
        },
        separator: {
          color: isLight ? tokens.neutral[400] : darkTokens.text.disabled,
        },
      },
    },
    MuiSwitch: {
      styleOverrides: {
        switchBase: {
          '&.Mui-checked': {
            color: isLight ? tokens.primary.main : darkTokens.primary.main,
            '& + .MuiSwitch-track': {
              backgroundColor: isLight ? tokens.primary[300] : darkTokens.primary.main,
              opacity: 0.6,
            },
          },
        },
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: {
          borderColor: surfaceBorder,
        },
      },
    },
  };
};

export const createDinamicaTheme = (mode: PaletteMode = 'light') => {
  const isLight = mode === 'light';

  return createTheme({
    palette: {
      mode,
      primary: {
        main: isLight ? tokens.primary.main : darkTokens.primary.main,
        dark: isLight ? tokens.primary[800] : darkTokens.primary.dark,
        light: isLight ? tokens.primary[300] : darkTokens.primary.light,
        contrastText: '#FFFFFF',
      },
      secondary: {
        main: isLight ? tokens.secondary.main : darkTokens.secondary.main,
        dark: isLight ? tokens.secondary.dark : darkTokens.secondary.dark,
        light: tokens.secondary.light,
        contrastText: tokens.primary[800],
      },
      success: {
        main: isLight ? tokens.success.main : darkTokens.success.main,
        light: isLight ? tokens.success.light : darkTokens.success.light,
        dark: tokens.success.dark,
        contrastText: '#FFFFFF',
      },
      warning: {
        main: isLight ? tokens.warning.main : darkTokens.warning.main,
        light: isLight ? tokens.warning.light : darkTokens.warning.light,
        dark: tokens.warning.dark,
        contrastText: tokens.primary[800],
      },
      error: {
        main: isLight ? tokens.error.main : darkTokens.error.main,
        light: isLight ? tokens.error.light : darkTokens.error.light,
        dark: tokens.error.dark,
        contrastText: '#FFFFFF',
      },
      info: {
        main: isLight ? tokens.info.main : darkTokens.info.main,
        light: isLight ? tokens.info.light : darkTokens.info.light,
        dark: tokens.info.dark,
        contrastText: '#FFFFFF',
      },
      background: {
        default: isLight ? tokens.neutral[50] : darkTokens.bg.default,
        paper: isLight ? '#FFFFFF' : darkTokens.bg.paper,
      },
      text: {
        primary: isLight ? tokens.neutral[800] : darkTokens.text.primary,
        secondary: isLight ? tokens.neutral[600] : darkTokens.text.secondary,
        disabled: isLight ? tokens.neutral[500] : darkTokens.text.disabled,
      },
      divider: isLight ? tokens.neutral[300] : darkTokens.border.default,
      action: {
        hover: isLight ? 'rgba(27,42,74,0.04)' : 'rgba(255,255,255,0.05)',
        selected: isLight ? 'rgba(27,42,74,0.08)' : 'rgba(255,255,255,0.1)',
        disabled: isLight ? tokens.neutral[400] : darkTokens.text.disabled,
        disabledBackground: isLight ? tokens.neutral[200] : 'rgba(255,255,255,0.08)',
      },
    },
    typography,
    spacing: 8,
    shape: {
      borderRadius: 8,
    },
    breakpoints: {
      values: {
        xs: 0,
        sm: 600,
        md: 900,
        lg: 1200,
        xl: 1536,
      },
    },
    shadows: customShadows as ThemeOptions['shadows'],
    components: getComponentOverrides(mode),
  });
};

export const lightTheme = createDinamicaTheme('light');
export const darkTheme = createDinamicaTheme('dark');

export { chartColors, statusColors };
