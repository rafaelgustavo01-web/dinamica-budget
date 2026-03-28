export const tokens = {
  primary: {
    900: '#0E1525',
    800: '#1B2A4A',
    700: '#243660',
    600: '#2D4276',
    main: '#1B3A6B',
    400: '#3A5490',
    300: '#5A7AB5',
    200: '#8AA4D0',
    100: '#B5C7E3',
    50: '#EDF1F8',
  },
  secondary: {
    dark: '#8B6209',
    main: '#E8A623',
    light: '#F0C05C',
    50: '#FDF3DD',
  },
  neutral: {
    50: '#F8F9FA',
    100: '#F1F3F5',
    200: '#E9ECEF',
    300: '#DEE2E6',
    400: '#ADB5BD',
    500: '#6C757D',
    600: '#495057',
    700: '#343A40',
    800: '#212529',
    900: '#121518',
  },
  success: {
    main: '#1B7A3D',
    light: '#D4EDDA',
    dark: '#155724',
  },
  warning: {
    main: '#E8A623',
    light: '#FFF3CD',
    dark: '#856404',
  },
  error: {
    main: '#C62828',
    light: '#F8D7DA',
    dark: '#721C24',
  },
  info: {
    main: '#1565C0',
    light: '#D1ECF1',
    dark: '#0D47A1',
  },
} as const;

export const darkTokens = {
  bg: {
    default: '#0E1420',
    paper: '#152032',
    alt: '#1B2A44',
  },
  border: {
    default: '#2A3A56',
    input: '#3D5070',
  },
  text: {
    primary: '#E1E5EB',
    secondary: '#8A95A8',
    disabled: '#5A6578',
  },
  primary: {
    main: '#5A8AD0',
    dark: '#1B3A6B',
    light: '#8AB0E8',
  },
  secondary: {
    main: '#F0B942',
    dark: '#E8A623',
  },
  success: {
    main: '#4CAF6E',
    light: 'rgba(76,175,110,0.15)',
  },
  warning: {
    main: '#F0B942',
    light: 'rgba(240,185,66,0.15)',
  },
  error: {
    main: '#EF5350',
    light: 'rgba(239,83,80,0.15)',
  },
  info: {
    main: '#5C9CE6',
    light: 'rgba(92,156,230,0.15)',
  },
} as const;

const elevatedShadow =
  '0px 20px 40px rgba(27,42,74,0.14), 0px 8px 16px rgba(27,42,74,0.08)';

export const customShadows = [
  'none',
  '0px 1px 3px rgba(27,42,74,0.08), 0px 1px 2px rgba(27,42,74,0.06)',
  '0px 2px 4px rgba(27,42,74,0.08), 0px 1px 3px rgba(27,42,74,0.06)',
  '0px 4px 6px rgba(27,42,74,0.08), 0px 2px 4px rgba(27,42,74,0.06)',
  '0px 6px 10px rgba(27,42,74,0.08), 0px 3px 6px rgba(27,42,74,0.06)',
  '0px 8px 16px rgba(27,42,74,0.08), 0px 4px 8px rgba(27,42,74,0.06)',
  '0px 10px 20px rgba(27,42,74,0.10), 0px 4px 8px rgba(27,42,74,0.06)',
  '0px 12px 24px rgba(27,42,74,0.10), 0px 5px 10px rgba(27,42,74,0.06)',
  '0px 14px 28px rgba(27,42,74,0.10), 0px 6px 12px rgba(27,42,74,0.06)',
  '0px 16px 32px rgba(27,42,74,0.12), 0px 6px 14px rgba(27,42,74,0.06)',
  '0px 18px 36px rgba(27,42,74,0.12), 0px 7px 16px rgba(27,42,74,0.06)',
  '0px 20px 40px rgba(27,42,74,0.12), 0px 8px 16px rgba(27,42,74,0.06)',
  elevatedShadow,
  ...Array(12).fill(elevatedShadow),
] as const;

export const chartColors = {
  light: [
    '#1B2A4A',
    '#1A7A7A',
    '#C48A1A',
    '#A85232',
    '#3A6EA5',
    '#5C7A3D',
    '#7A3D6E',
    '#546E7A',
  ],
  dark: [
    '#7A9AD0',
    '#4DB8B8',
    '#F0B942',
    '#D4845A',
    '#6FA3D4',
    '#8AB566',
    '#B86FA5',
    '#90A4AE',
  ],
} as const;

export const statusColors = {
  light: {
    aprovado: { bg: '#D4EDDA', color: '#155724' },
    pendente: { bg: '#FFF3CD', color: '#856404' },
    rejeitado: { bg: '#F8D7DA', color: '#721C24' },
    rascunho: { bg: '#E9ECEF', color: '#495057' },
    'em-revisao': { bg: '#D1ECF1', color: '#0D47A1' },
    ativo: { bg: '#1B3A6B', color: '#FFFFFF' },
    inativo: { bg: '#E9ECEF', color: '#6C757D' },
    tcpo: { bg: '#EAF0F9', color: '#1B3A6B' },
    propria: { bg: '#F2EBFF', color: '#6941C6' },
  },
  dark: {
    aprovado: { bg: 'rgba(76,175,110,0.15)', color: '#4CAF6E' },
    pendente: { bg: 'rgba(240,185,66,0.15)', color: '#F0B942' },
    rejeitado: { bg: 'rgba(239,83,80,0.15)', color: '#EF5350' },
    rascunho: { bg: 'rgba(255,255,255,0.08)', color: '#8A95A8' },
    'em-revisao': { bg: 'rgba(92,156,230,0.15)', color: '#5C9CE6' },
    ativo: { bg: 'rgba(90,138,208,0.2)', color: '#5A8AD0' },
    inativo: { bg: 'rgba(255,255,255,0.05)', color: '#5A6578' },
    tcpo: { bg: 'rgba(90,138,208,0.18)', color: '#8AB0E8' },
    propria: { bg: 'rgba(105,65,198,0.18)', color: '#C9B5FF' },
  },
} as const;

export const fonts = {
  primary:
    '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  display: '"DM Sans", "Inter", sans-serif',
  mono: '"JetBrains Mono", "Fira Code", "Consolas", monospace',
} as const;
