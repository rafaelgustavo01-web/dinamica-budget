import { apiClient } from './apiClient';
import type {
  HistogramaCompletoResponse,
  MontarHistogramaResponse,
  RecursoExtraCreate,
  RecursoExtraOut,
  RecursoExtraUpdate,
  AlocarRecursoRequest,
  AlocacaoOut,
} from '../../types/contracts/proposta_pc';

export const histogramaApi = {
  async montarHistograma(propostaId: string) {
    const { data } = await apiClient.post<MontarHistogramaResponse>(
      `/propostas/${propostaId}/montar-histograma`
    );
    return data;
  },

  async getHistograma(propostaId: string) {
    const { data } = await apiClient.get<HistogramaCompletoResponse>(
      `/propostas/${propostaId}/histograma`
    );
    return data;
  },

  async editarItem(propostaId: string, tabela: string, itemId: string, payload: Record<string, any>) {
    const { data } = await apiClient.patch(
      `/propostas/${propostaId}/histograma/${tabela}/${itemId}`,
      payload
    );
    return data;
  },

  async aceitarBcu(propostaId: string, tabela: string, itemId: string) {
    const { data } = await apiClient.post(
      `/propostas/${propostaId}/histograma/${tabela}/${itemId}/aceitar-bcu`
    );
    return data;
  },

  async criarRecursoExtra(propostaId: string, payload: RecursoExtraCreate) {
    const { data } = await apiClient.post<RecursoExtraOut>(
      `/propostas/${propostaId}/recursos-extras`,
      payload
    );
    return data;
  },

  async listarRecursosExtras(propostaId: string) {
    const { data } = await apiClient.get<RecursoExtraOut[]>(
      `/propostas/${propostaId}/recursos-extras`
    );
    return data;
  },

  async atualizarRecursoExtra(propostaId: string, recursoId: string, payload: RecursoExtraUpdate) {
    const { data } = await apiClient.patch<RecursoExtraOut>(
      `/propostas/${propostaId}/recursos-extras/${recursoId}`,
      payload
    );
    return data;
  },

  async deletarRecursoExtra(propostaId: string, recursoId: string) {
    await apiClient.delete(`/propostas/${propostaId}/recursos-extras/${recursoId}`);
  },

  async alocarRecurso(propostaId: string, composicaoId: string, payload: AlocarRecursoRequest) {
    const { data } = await apiClient.post<AlocacaoOut>(
      `/propostas/${propostaId}/composicoes/${composicaoId}/alocar-recurso`,
      payload
    );
    return data;
  },

  async desalocarRecurso(propostaId: string, alocacaoId: string) {
    await apiClient.delete(`/propostas/${propostaId}/alocacoes/${alocacaoId}`);
  },
};
