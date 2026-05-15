import axios, {
  AxiosError,
  type InternalAxiosRequestConfig,
} from 'axios';

import type { ApiErrorPayload, ApiErrorWithRequestId } from '../../types/contracts/common';
import {
  clearSessionTokens,
  persistSessionTokens,
  readSessionTokens,
} from '../../utils/storage';

export const API_BASE_URL = import.meta.env.VITE_API_URL ?? '/api/v1';
export const SESSION_EXPIRED_EVENT = 'dinamica-budget:session-expired';

export const publicApiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

type RetryRequestConfig = InternalAxiosRequestConfig & { _retry?: boolean };

let refreshPromise: Promise<string | null> | null = null;


function createClientRequestId() {
  const cryptoApi = window.crypto;
  if (cryptoApi?.randomUUID) {
    return 'web_' + cryptoApi.randomUUID().replaceAll('-', '').slice(0, 12);
  }
  return 'web_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8);
}

function getApiErrorRequestId(data: unknown): string | null {
  if (!data || typeof data !== 'object') {
    return null;
  }

  const payload = data as Partial<ApiErrorPayload & ApiErrorWithRequestId>;
  if (typeof payload.request_id === 'string' && payload.request_id) {
    return payload.request_id;
  }
  if (payload.error && typeof payload.error.request_id === 'string' && payload.error.request_id) {
    return payload.error.request_id;
  }

  return null;
}

function appendRequestId(message: string, requestId: string | null) {
  return requestId ? message + ' Código: ' + requestId : message;
}

async function refreshAccessToken() {
  const currentSession = readSessionTokens();

  if (!currentSession?.refreshToken) {
    clearSessionTokens();
    window.dispatchEvent(new CustomEvent(SESSION_EXPIRED_EVENT));
    return null;
  }

  if (!refreshPromise) {
    refreshPromise = publicApiClient
      .post('/auth/refresh', {
        refresh_token: currentSession.refreshToken,
      })
      .then((response) => {
        const payload = response.data as {
          access_token: string;
          refresh_token: string;
          token_type: string;
          expires_in: number;
        };

        persistSessionTokens({
          accessToken: payload.access_token,
          refreshToken: payload.refresh_token,
          tokenType: payload.token_type,
          expiresIn: payload.expires_in,
        });

        return payload.access_token;
      })
      .catch((error) => {
        clearSessionTokens();
        window.dispatchEvent(new CustomEvent(SESSION_EXPIRED_EVENT));
        throw error;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

apiClient.interceptors.request.use((config) => {
  const currentSession = readSessionTokens();

  // Normalize GET requests to the servicos list endpoint so the
  // backend receives the trailing slash and returns JSON (prevents SPA fallback).
  try {
    const method = (config.method || '').toString().toLowerCase();
    const url = typeof config.url === 'string' ? config.url : '';
    if (method === 'get') {
      // handle both '/servicos' and 'servicos' forms without corrupting query strings
      const [path, query] = url.split('?');
      if (/^\/?servicos\/?$/.test(path)) {
        config.url = '/servicos/' + (query ? '?' + query : '');
      }
    }

    // NOTE: do not add trailing slashes for non-GET methods — FastAPI
    // treats routes with/without trailing slash as distinct and POST
    // on the slash version can return 405. Keep POST/PUT/PATCH/DELETE
    // requests as the client originally specified.
  } catch {
    // non-fatal: proceed with original config
  }

  config.headers['X-Client-Request-ID'] = createClientRequestId();

  // Let the browser set multipart boundaries for uploads.
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type'];
  }

  if (currentSession?.accessToken) {
    config.headers.Authorization = `Bearer ${currentSession.accessToken}`;
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const requestConfig = error.config as RetryRequestConfig | undefined;
    const requestUrl =
      typeof requestConfig?.url === 'string' ? requestConfig.url : '';

    if (
      error.response?.status === 401 &&
      requestConfig &&
      !requestConfig._retry &&
      !requestUrl.includes('/auth/login') &&
      !requestUrl.includes('/auth/refresh')
    ) {
      requestConfig._retry = true;

      try {
        const nextAccessToken = await refreshAccessToken();

        if (nextAccessToken) {
          requestConfig.headers.Authorization = `Bearer ${nextAccessToken}`;
          return apiClient(requestConfig);
        }
      } catch {
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  },
);

function isApiErrorPayload(data: unknown): data is ApiErrorPayload {
  return Boolean(
    data &&
      typeof data === 'object' &&
      'error' in data &&
      data.error &&
      typeof data.error === 'object' &&
      'message' in data.error,
  );
}

function extractFastApiValidationMessage(data: unknown): string | null {
  if (!data || typeof data !== 'object' || !('detail' in data)) {
    return null;
  }

  const detail = (data as { detail?: unknown }).detail;
  if (typeof detail === 'string' && detail) {
    return detail;
  }

  if (Array.isArray(detail) && detail.length) {
    const first = detail[0];
    if (first && typeof first === 'object' && 'msg' in first) {
      const message = (first as { msg?: unknown }).msg;
      if (typeof message === 'string' && message) {
        return message;
      }
    }
  }

  return null;
}

export function extractApiErrorRequestId(error: unknown): string | null {
  if (axios.isAxiosError(error)) {
    return getApiErrorRequestId(error.response?.data);
  }

  return null;
}

export function extractApiErrorMessage(
  error: unknown,
  fallback = 'Falha ao processar a operação.',
) {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data;
    const requestId = getApiErrorRequestId(data);
    const validationMessage = extractFastApiValidationMessage(data);
    if (validationMessage) {
      return appendRequestId(validationMessage, requestId);
    }
    if (isApiErrorPayload(data)) {
      return appendRequestId(data.error.message, requestId);
    }
    if (typeof error.message === 'string' && error.message) {
      return appendRequestId(error.message, requestId);
    }
    return appendRequestId(fallback, requestId);
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
}

export { apiClient };
