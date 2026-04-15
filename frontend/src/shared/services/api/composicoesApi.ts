import type {
  AdicionarComponenteRequest,
  ClonarComposicaoRequest,
} from '../../types/contracts/composicoes';
import type { ExplodeComposicaoResponse } from '../../types/contracts/servicos';
import { apiClient } from './apiClient';

export const composicoesApi = {
  async clonar(payload: ClonarComposicaoRequest): Promise<ExplodeComposicaoResponse> {
    const response = await apiClient.post<ExplodeComposicaoResponse>(
      '/composicoes/clonar',
      payload,
    );
    return response.data;
  },

  async adicionarComponente(
    paiId: string,
    payload: AdicionarComponenteRequest,
  ): Promise<ExplodeComposicaoResponse> {
    const response = await apiClient.post<ExplodeComposicaoResponse>(
      `/composicoes/${paiId}/componentes`,
      payload,
    );
    return response.data;
  },

  async removerComponente(paiId: string, componenteId: string): Promise<void> {
    await apiClient.delete(`/composicoes/${paiId}/componentes/${componenteId}`);
  },
};
