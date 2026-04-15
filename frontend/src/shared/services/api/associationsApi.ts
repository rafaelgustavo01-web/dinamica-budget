import type { PaginatedResponse } from '../../types/contracts/common';
import type {
  AssociacaoListItem,
  AssociacaoListParams,
} from '../../types/contracts/associacoes';
import { apiClient } from './apiClient';

export const associationsApi = {
  async list(params: AssociacaoListParams) {
    const response = await apiClient.get<PaginatedResponse<AssociacaoListItem>>(
      '/busca/associacoes',
      { params },
    );
    return response.data;
  },

  async remove(associacaoId: string) {
    await apiClient.delete(`/busca/associacoes/${associacaoId}`);
  },
};
