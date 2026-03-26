import type { PaginatedResponse } from '../../types/contracts/common';
import type {
  ClienteCreateRequest,
  ClienteListParams,
  ClienteResponse,
} from '../../types/contracts/clientes';
import { apiClient } from './apiClient';

export const clientsApi = {
  async list(params: ClienteListParams) {
    const response = await apiClient.get<PaginatedResponse<ClienteResponse>>('/clientes/', {
      params,
    });
    return response.data;
  },

  async create(payload: ClienteCreateRequest) {
    const response = await apiClient.post<ClienteResponse>('/clientes/', payload);
    return response.data;
  },
};
