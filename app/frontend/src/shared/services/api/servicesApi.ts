import type { PaginatedResponse } from '../../types/contracts/common';
import type {
  ComposicaoComponenteResponse,
  ExplodeComposicaoResponse,
  ServicoCreate,
  ServicoListParams,
  ServicoTcpoResponse,
} from '../../types/contracts/servicos';
import { apiClient } from './apiClient';

export const servicesApi = {
  async list(params: ServicoListParams) {
    const response = await apiClient.get<PaginatedResponse<ServicoTcpoResponse>>(
      '/servicos/',
      { params },
    );
    return response.data;
  },

  async getById(servicoId: string) {
    const response = await apiClient.get<ServicoTcpoResponse>(`/servicos/${servicoId}`);
    return response.data;
  },

  async getComposicao(servicoId: string) {
    const response = await apiClient.get<ExplodeComposicaoResponse>(
      `/servicos/${servicoId}/composicao`,
    );
    return response.data;
  },

  async getComponentes(servicoId: string) {
    const response = await apiClient.get<ComposicaoComponenteResponse[]>(
      `/servicos/${servicoId}/componentes`,
    );
    return response.data;
  },

  async create(payload: ServicoCreate) {
    const response = await apiClient.post<ServicoTcpoResponse>('/servicos/', payload);
    return response.data;
  },
};
