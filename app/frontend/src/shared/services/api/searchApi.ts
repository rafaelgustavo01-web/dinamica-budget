import type {
  AssociacaoResponse,
  BuscaServicoRequest,
  BuscaServicoResponse,
  CriarAssociacaoRequest,
} from '../../types/contracts/busca';
import { apiClient } from './apiClient';

export const searchApi = {
  async buscar(payload: BuscaServicoRequest) {
    const response = await apiClient.post<BuscaServicoResponse>('/busca/servicos', payload);
    return response.data;
  },

  async associar(payload: CriarAssociacaoRequest) {
    const response = await apiClient.post<AssociacaoResponse>('/busca/associar', payload);
    return response.data;
  },
};
