import type {
  AprovarHomologacaoRequest,
  AprovarHomologacaoResponse,
  CriarItemProprioRequest,
  CriarItemProprioResponse,
  PendentesHomologacaoResponse,
} from '../../types/contracts/homologacao';
import { apiClient } from './apiClient';

export const homologationApi = {
  async listPendentes(clienteId: string, page: number, pageSize: number) {
    const response = await apiClient.get<PendentesHomologacaoResponse>(
      '/homologacao/pendentes',
      {
        params: {
          cliente_id: clienteId,
          page,
          page_size: pageSize,
        },
      },
    );
    return response.data;
  },

  async aprovar(payload: AprovarHomologacaoRequest) {
    const response = await apiClient.post<AprovarHomologacaoResponse>(
      '/homologacao/aprovar',
      payload,
    );
    return response.data;
  },

  async criarItemProprio(payload: CriarItemProprioRequest) {
    const response = await apiClient.post<CriarItemProprioResponse>(
      '/homologacao/itens-proprios',
      payload,
    );
    return response.data;
  },
};
