import { apiClient } from './apiClient';
import type { PaginatedResponse } from '../../types/contracts/common';

export type StatusProposta =
  | 'RASCUNHO'
  | 'EM_ANALISE'
  | 'CPU_GERADA'
  | 'APROVADA'
  | 'REPROVADA'
  | 'ARQUIVADA';

export interface PropostaResponse {
  id: string;
  cliente_id: string;
  criado_por_id: string;
  codigo: string;
  titulo: string | null;
  descricao: string | null;
  status: StatusProposta;
  versao_cpu: number;
  pc_cabecalho_id: string | null;
  total_direto: number | null;
  total_indireto: number | null;
  total_geral: number | null;
  data_finalizacao: string | null;
  created_at: string;
  updated_at: string;
}

export interface PropostaCreateRequest {
  cliente_id: string;
  titulo?: string;
  descricao?: string;
}

export interface PropostaUpdateRequest {
  titulo?: string;
  descricao?: string;
}

export interface PqImportacaoResponse {
  importacao_id: string;
  status: string;
  linhas_total: number;
  linhas_importadas: number;
  linhas_com_erro: number;
}

export interface PqMatchResponse {
  processados: number;
  sugeridos: number;
  sem_match: number;
}

export const proposalsApi = {
  async list(clienteId: string, page = 1, pageSize = 20) {
    const response = await apiClient.get<PaginatedResponse<PropostaResponse>>('/propostas/', {
      params: {
        cliente_id: clienteId,
        page,
        page_size: pageSize,
      },
    });
    return response.data;
  },

  async getById(propostaId: string) {
    const response = await apiClient.get<PropostaResponse>(`/propostas/${propostaId}`);
    return response.data;
  },

  async create(payload: PropostaCreateRequest) {
    const response = await apiClient.post<PropostaResponse>('/propostas/', payload);
    return response.data;
  },

  async update(propostaId: string, payload: PropostaUpdateRequest) {
    const response = await apiClient.patch<PropostaResponse>(`/propostas/${propostaId}`, payload);
    return response.data;
  },

  async delete(propostaId: string) {
    await apiClient.delete(`/propostas/${propostaId}`);
  },

  async uploadPq(propostaId: string, file: File) {
    const formData = new FormData();
    formData.append('arquivo', file);
    const response = await apiClient.post<PqImportacaoResponse>(
      `/propostas/${propostaId}/pq/importar`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      },
    );
    return response.data;
  },

  async executeMatch(propostaId: string) {
    const response = await apiClient.post<PqMatchResponse>(`/propostas/${propostaId}/pq/match`);
    return response.data;
  },
};
