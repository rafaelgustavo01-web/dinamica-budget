import { apiClient } from './apiClient';

export interface DeParaListItem {
  id: string | null;
  base_tcpo_id: string;
  base_tcpo_codigo: string;
  base_tcpo_descricao: string;
  base_tcpo_tipo_recurso: string | null;
  bcu_table_type: string | null;
  bcu_item_id: string | null;
  bcu_item_descricao: string | null;
}

export interface DeParaOut {
  id: string;
  base_tcpo_id: string;
  bcu_table_type: string;
  bcu_item_id: string;
  criado_por_id: string | null;
  criado_em: string;
}

export interface DeParaCreatePayload {
  base_tcpo_id: string;
  bcu_table_type: string;
  bcu_item_id: string;
}

export const bcuDeParaApi = {
  async listar(params?: { only_unmapped?: boolean; search?: string }): Promise<DeParaListItem[]> {
    const r = await apiClient.get<DeParaListItem[]>('/bcu/de-para', { params });
    return r.data;
  },

  async criar(payload: DeParaCreatePayload): Promise<DeParaOut> {
    const r = await apiClient.post<DeParaOut>('/bcu/de-para', payload);
    return r.data;
  },

  async atualizar(deParaId: string, payload: DeParaCreatePayload): Promise<DeParaOut> {
    const r = await apiClient.patch<DeParaOut>(`/bcu/de-para/${deParaId}`, payload);
    return r.data;
  },

  async deletar(deParaId: string): Promise<void> {
    await apiClient.delete(`/bcu/de-para/${deParaId}`);
  },
};
