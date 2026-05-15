export type DecimalValue = number | string;

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ApiErrorPayload {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown> | null;
    request_id?: string;
  };
  request_id?: string;
}

export interface ApiErrorWithRequestId {
  detail?: unknown;
  request_id?: string;
}
