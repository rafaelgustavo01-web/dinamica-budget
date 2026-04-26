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

export type StatusMatch =
  | 'PENDENTE'
  | 'BUSCANDO'
  | 'SUGERIDO'
  | 'CONFIRMADO'
  | 'MANUAL'
  | 'SEM_MATCH';

export type TipoServicoMatch = 'ITEM_PROPRIO' | 'BASE_TCPO';

export type AcaoMatch = 'confirmar' | 'substituir' | 'rejeitar';

export interface PqItemResponse {
  id: string;
  proposta_id: string;
  pq_importacao_id: string | null;
  codigo_original: string | null;
  descricao_original: string;
  unidade_medida_original: string | null;
  quantidade_original: string | null;
  match_status: StatusMatch;
  match_confidence: string | null;
  servico_match_id: string | null;
  servico_match_tipo: TipoServicoMatch | null;
  linha_planilha: number | null;
  observacao: string | null;
  created_at: string;
  updated_at: string;
}

export interface PqMatchConfirmarRequest {
  acao: AcaoMatch;
  servico_match_id?: string;
  servico_match_tipo?: TipoServicoMatch;
  quantidade?: string;
}

export interface ComposicaoDetalhe {
  id: string;
  proposta_item_id: string;
  descricao_insumo: string;
  unidade_medida: string;
  quantidade_consumo: string;
  custo_unitario_insumo: string | null;
  custo_total_insumo: string | null;
  tipo_recurso: string | null;
  nivel: number;
  e_composicao: boolean;
  fonte_custo: string | null;
}

export interface CpuItemDetalhado {
  id: string;
  proposta_id: string;
  pq_item_id: string | null;
  servico_id: string;
  codigo: string;
  descricao: string;
  unidade_medida: string;
  quantidade: string;
  custo_material_unitario: string | null;
  custo_mao_obra_unitario: string | null;
  custo_equipamento_unitario: string | null;
  custo_direto_unitario: string | null;
  percentual_indireto: string | null;
  custo_indireto_unitario: string | null;
  preco_unitario: string | null;
  preco_total: string | null;
  composicao_fonte: string | null;
  ordem: number;
}

export interface RecalcularBdiRequest {
  percentual_bdi: number;
}

export interface RecalcularBdiResponse {
  proposta_id: string;
  percentual_bdi: number;
  total_direto: number;
  total_indireto: number;
  total_geral: number;
  itens_recalculados: number;
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

  async listPqItens(propostaId: string, statusMatch?: StatusMatch): Promise<PqItemResponse[]> {
    const params = statusMatch ? { status_match: statusMatch } : undefined;
    const response = await apiClient.get<PqItemResponse[]>(
      `/propostas/${propostaId}/pq/itens`,
      { params },
    );
    return response.data;
  },

  async confirmarMatch(
    propostaId: string,
    itemId: string,
    payload: PqMatchConfirmarRequest,
  ): Promise<PqItemResponse> {
    const response = await apiClient.patch<PqItemResponse>(
      `/propostas/${propostaId}/pq/itens/${itemId}/match`,
      payload,
    );
    return response.data;
  },

  async listCpuItens(propostaId: string) {
    const response = await apiClient.get<CpuItemDetalhado[]>(
      `/propostas/${propostaId}/cpu/itens`,
    );
    return response.data;
  },

  async getComposicoes(propostaId: string, itemId: string) {
    const response = await apiClient.get<ComposicaoDetalhe[]>(
      `/propostas/${propostaId}/cpu/itens/${itemId}/composicoes`,
    );
    return response.data;
  },

  async recalcularBdi(
    propostaId: string,
    payload: RecalcularBdiRequest,
  ) {
    const response = await apiClient.post<RecalcularBdiResponse>(
      `/propostas/${propostaId}/cpu/recalcular-bdi`,
      payload,
    );
    return response.data;
  },

  async gerarCpu(
    propostaId: string,
    percentualBdi: number,
    pcCabecalhoId?: string,
  ) {
    const params: Record<string, string | number> = { percentual_bdi: percentualBdi };
    if (pcCabecalhoId) params.pc_cabecalho_id = pcCabecalhoId;
    const response = await apiClient.post(
      `/propostas/${propostaId}/cpu/gerar`,
      null,
      { params },
    );
    return response.data;
  },

  async exportExcel(propostaId: string): Promise<Blob> {
    const response = await apiClient.get(`/propostas/${propostaId}/export/excel`, {
      responseType: 'blob',
    });
    return response.data as Blob;
  },

  async exportPdf(propostaId: string): Promise<Blob> {
    const response = await apiClient.get(`/propostas/${propostaId}/export/pdf`, {
      responseType: 'blob',
    });
    return response.data as Blob;
  },
};
