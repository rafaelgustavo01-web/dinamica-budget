import {
  createContext,
  type PropsWithChildren,
  useContext,
  useMemo,
  useState,
} from 'react';

type ColorMode = 'light' | 'dark';

interface ColorModeContextValue {
  mode: ColorMode;
  toggleColorMode: () => void;
  setColorMode: (mode: ColorMode) => void;
}

const STORAGE_KEY = 'theme-mode';

const ColorModeContext = createContext<ColorModeContextValue | null>(null);

export function ColorModeProvider({ children }: PropsWithChildren) {
  const [mode, setMode] = useState<ColorMode>(() => {
    if (typeof window === 'undefined') {
      return 'light';
    }

    const stored = window.localStorage.getItem(STORAGE_KEY);
    return stored === 'dark' ? 'dark' : 'light';
  });

  const value = useMemo<ColorModeContextValue>(
    () => ({
      mode,
      toggleColorMode() {
        setMode((current) => {
          const next = current === 'light' ? 'dark' : 'light';
          window.localStorage.setItem(STORAGE_KEY, next);
          return next;
        });
      },
      setColorMode(nextMode) {
        window.localStorage.setItem(STORAGE_KEY, nextMode);
        setMode(nextMode);
      },
    }),
    [mode],
  );

  return <ColorModeContext.Provider value={value}>{children}</ColorModeContext.Provider>;
}

export function useColorMode() {
  const context = useContext(ColorModeContext);

  if (!context) {
    throw new Error('useColorMode must be used within ColorModeProvider.');
  }

  return context;
}
