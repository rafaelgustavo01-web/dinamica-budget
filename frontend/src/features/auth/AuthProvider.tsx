import {
  createContext,
  type PropsWithChildren,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { useNavigate } from 'react-router-dom';

import { authApi } from '../../shared/services/api/authApi';
import { SESSION_EXPIRED_EVENT } from '../../shared/services/api/apiClient';
import type { LoginRequest, MeResponse } from '../../shared/types/contracts/auth';
import {
  clearSessionTokens,
  persistSelectedClientId,
  persistSessionTokens,
  readSelectedClientId,
  readSessionTokens,
} from '../../shared/utils/storage';
import { getAvailableClientIds } from '../../shared/utils/permissions';

interface AuthContextValue {
  user: MeResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  selectedClientId: string;
  availableClientIds: string[];
  login: (payload: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  setSelectedClientId: (clienteId: string) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function syncSelectedClient(
  user: MeResponse | null,
  setSelectedClient: (value: string) => void,
) {
  const storedClientId = readSelectedClientId().trim();
  const availableClientIds = getAvailableClientIds(user);
  const nextClientId =
    storedClientId && (user?.is_admin || availableClientIds.includes(storedClientId))
      ? storedClientId
      : availableClientIds[0] ?? '';

  setSelectedClient(nextClientId);
  persistSelectedClientId(nextClientId);
}

export function AuthProvider({ children }: PropsWithChildren) {
  const [user, setUser] = useState<MeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedClientIdState, setSelectedClientIdState] = useState('');
  const navigate = useNavigate();

  const availableClientIds = useMemo(() => getAvailableClientIds(user), [user]);

  const resetSession = useCallback(() => {
    clearSessionTokens();
    persistSelectedClientId('');
    setUser(null);
    setSelectedClientIdState('');
  }, []);

  const refreshUser = useCallback(async () => {
    const me = await authApi.getMe();
    setUser(me);
    syncSelectedClient(me, setSelectedClientIdState);
  }, []);

  useEffect(() => {
    let active = true;

    const initializeSession = async () => {
      const session = readSessionTokens();

      if (!session) {
        if (active) {
          setIsLoading(false);
        }
        return;
      }

      try {
        const me = await authApi.getMe();
        if (!active) {
          return;
        }
        setUser(me);
        syncSelectedClient(me, setSelectedClientIdState);
      } catch {
        if (active) {
          resetSession();
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    };

    const handleSessionExpired = () => {
      resetSession();
      navigate('/login', { replace: true });
    };

    window.addEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);
    void initializeSession();

    return () => {
      active = false;
      window.removeEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);
    };
  }, [navigate, resetSession]);

  const login = useCallback(async (payload: LoginRequest) => {
    const tokens = await authApi.login(payload);
    persistSessionTokens({
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      tokenType: tokens.token_type,
      expiresIn: tokens.expires_in,
    });

    const me = await authApi.getMe();
    setUser(me);
    syncSelectedClient(me, setSelectedClientIdState);
  }, []);

  const logout = useCallback(async () => {
    try {
      if (user) {
        await authApi.logout();
      }
    } finally {
      resetSession();
    }
  }, [resetSession, user]);

  const setSelectedClientId = useCallback(
    (clienteId: string) => {
      const normalized = clienteId.trim();

      if (!normalized) {
        setSelectedClientIdState('');
        persistSelectedClientId('');
        return;
      }

      if (!user?.is_admin && !availableClientIds.includes(normalized)) {
        return;
      }

      setSelectedClientIdState(normalized);
      persistSelectedClientId(normalized);
    },
    [availableClientIds, user?.is_admin],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      isLoading,
      selectedClientId: selectedClientIdState,
      availableClientIds,
      login,
      logout,
      refreshUser,
      setSelectedClientId,
    }),
    [
      availableClientIds,
      isLoading,
      login,
      logout,
      refreshUser,
      selectedClientIdState,
      setSelectedClientId,
      user,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within AuthProvider.');
  }

  return context;
}
