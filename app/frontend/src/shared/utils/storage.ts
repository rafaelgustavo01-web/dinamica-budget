const STORAGE_KEYS = {
  accessToken: 'dinamica-budget.access-token',
  refreshToken: 'dinamica-budget.refresh-token',
  tokenType: 'dinamica-budget.token-type',
  expiresAt: 'dinamica-budget.expires-at',
  selectedClientId: 'dinamica-budget.selected-client-id',
} as const;

export interface PersistedSessionTokens {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresAt: number;
}

export interface PersistSessionInput {
  accessToken: string;
  refreshToken: string;
  tokenType?: string;
  expiresIn: number;
}

export function persistSessionTokens(input: PersistSessionInput) {
  const expiresAt = Date.now() + input.expiresIn * 1_000;
  localStorage.setItem(STORAGE_KEYS.accessToken, input.accessToken);
  localStorage.setItem(STORAGE_KEYS.refreshToken, input.refreshToken);
  localStorage.setItem(STORAGE_KEYS.tokenType, input.tokenType ?? 'bearer');
  localStorage.setItem(STORAGE_KEYS.expiresAt, String(expiresAt));
}

export function readSessionTokens(): PersistedSessionTokens | null {
  const accessToken = localStorage.getItem(STORAGE_KEYS.accessToken);
  const refreshToken = localStorage.getItem(STORAGE_KEYS.refreshToken);
  const tokenType = localStorage.getItem(STORAGE_KEYS.tokenType);
  const expiresAt = localStorage.getItem(STORAGE_KEYS.expiresAt);

  if (!accessToken || !refreshToken || !tokenType || !expiresAt) {
    return null;
  }

  return {
    accessToken,
    refreshToken,
    tokenType,
    expiresAt: Number(expiresAt),
  };
}

export function clearSessionTokens() {
  localStorage.removeItem(STORAGE_KEYS.accessToken);
  localStorage.removeItem(STORAGE_KEYS.refreshToken);
  localStorage.removeItem(STORAGE_KEYS.tokenType);
  localStorage.removeItem(STORAGE_KEYS.expiresAt);
}

export function readSelectedClientId() {
  return localStorage.getItem(STORAGE_KEYS.selectedClientId) ?? '';
}

export function persistSelectedClientId(clienteId: string) {
  if (clienteId) {
    localStorage.setItem(STORAGE_KEYS.selectedClientId, clienteId);
    return;
  }
  localStorage.removeItem(STORAGE_KEYS.selectedClientId);
}
