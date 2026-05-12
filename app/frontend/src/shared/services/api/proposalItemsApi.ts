import { apiClient } from './apiClient';

export interface ProposalItem {
  id: string;
  proposta_id: string;
  codigo: string;
  descricao: string;
  unidade_medida: string;
  quantidade: number;
  valor_unitario?: number;
  valor_total?: number;
  ordem?: number;
}

export interface AddItemRequest {
  codigo: string;
  descricao: string;
  unidade_medida: string;
  quantidade: number;
}

export interface UpdateItemRequest {
  descricao?: string;
  quantidade?: number;
  unidade_medida?: string;
}

export interface ItemTipo {
  id: string;
  label: string;
  descricao: string;
  campos: string[];
}

export interface BcuItem {
  id: string;
  codigo: string;
  descricao: string;
  valor: number;
}

export interface AddBcuItemRequest {
  bcu_item_id: string;
  quantidade: number;
}

export const proposalItemsApi = {
  /**
   * Lista todos os items de uma proposta
   */
  async listItems(propostaId: string): Promise<ProposalItem[]> {
    const response = await apiClient.get(`/propostas/${propostaId}/items`);
    return response.data;
  },

  /**
   * Adiciona um novo item à proposta
   */
  async addItem(propostaId: string, body: AddItemRequest): Promise<ProposalItem> {
    const response = await apiClient.post(`/propostas/${propostaId}/items`, body);
    return response.data;
  },

  /**
   * Atualiza um item existente
   */
  async updateItem(propostaId: string, itemId: string, body: UpdateItemRequest): Promise<ProposalItem> {
    const response = await apiClient.patch(`/propostas/${propostaId}/items/${itemId}`, body);
    return response.data;
  },

  /**
   * Remove um item da proposta
   */
  async deleteItem(propostaId: string, itemId: string): Promise<void> {
    await apiClient.delete(`/propostas/${propostaId}/items/${itemId}`);
  },

  /**
   * Reordena items da proposta
   */
  async reorderItems(propostaId: string, itemIds: string[]): Promise<{ success: boolean; items: ProposalItem[] }> {
    const response = await apiClient.post(`/propostas/${propostaId}/items/reordenar`, { items_ids: itemIds });
    return response.data;
  },

  /**
   * Lista tipos de items que podem ser adicionados
   */
  async listItemTipos(propostaId: string): Promise<{ tipos: ItemTipo[] }> {
    const response = await apiClient.get(`/propostas/${propostaId}/items/tipos`);
    return response.data;
  },

  /**
   * Lista mão de obra disponível na base de custos
   */
  async listMaoObra(propostaId: string): Promise<BcuItem[]> {
    const response = await apiClient.get(`/propostas/${propostaId}/items/bcu/mao-obra`);
    return response.data;
  },

  /**
   * Lista EPI disponível na base de custos
   */
  async listEpi(propostaId: string): Promise<BcuItem[]> {
    const response = await apiClient.get(`/propostas/${propostaId}/items/bcu/epi`);
    return response.data;
  },

  /**
   * Lista equipamentos disponíveis na base de custos
   */
  async listEquipamento(propostaId: string): Promise<BcuItem[]> {
    const response = await apiClient.get(`/propostas/${propostaId}/items/bcu/equipamento`);
    return response.data;
  },

  /**
   * Lista ferramentas disponíveis na base de custos
   */
  async listFerramenta(propostaId: string): Promise<BcuItem[]> {
    const response = await apiClient.get(`/propostas/${propostaId}/items/bcu/ferramenta`);
    return response.data;
  },

  /**
   * Adiciona mão de obra da base BCU
   */
  async addMaoObra(propostaId: string, body: AddBcuItemRequest): Promise<ProposalItem> {
    const response = await apiClient.post(`/propostas/${propostaId}/items/mao-obra`, body);
    return response.data;
  },

  /**
   * Adiciona EPI da base BCU
   */
  async addEpi(propostaId: string, body: AddBcuItemRequest): Promise<ProposalItem> {
    const response = await apiClient.post(`/propostas/${propostaId}/items/epi`, body);
    return response.data;
  },

  /**
   * Adiciona equipamento da base BCU
   */
  async addEquipamento(propostaId: string, body: AddBcuItemRequest): Promise<ProposalItem> {
    const response = await apiClient.post(`/propostas/${propostaId}/items/equipamento`, body);
    return response.data;
  },

  /**
   * Adiciona ferramenta da base BCU
   */
  async addFerramenta(propostaId: string, body: AddBcuItemRequest): Promise<ProposalItem> {
    const response = await apiClient.post(`/propostas/${propostaId}/items/ferramenta`, body);
    return response.data;
  },
};

