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
    return apiClient.get(`/propostas/${propostaId}/items`);
  },

  /**
   * Adiciona um novo item à proposta
   */
  async addItem(propostaId: string, body: AddItemRequest): Promise<ProposalItem> {
    return apiClient.post(`/propostas/${propostaId}/items`, body);
  },

  /**
   * Atualiza um item existente
   */
  async updateItem(propostaId: string, itemId: string, body: UpdateItemRequest): Promise<ProposalItem> {
    return apiClient.patch(`/propostas/${propostaId}/items/${itemId}`, body);
  },

  /**
   * Remove um item da proposta
   */
  async deleteItem(propostaId: string, itemId: string): Promise<void> {
    return apiClient.delete(`/propostas/${propostaId}/items/${itemId}`);
  },

  /**
   * Reordena items da proposta
   */
  async reorderItems(propostaId: string, itemIds: string[]): Promise<{ success: boolean; items: ProposalItem[] }> {
    return apiClient.post(`/propostas/${propostaId}/items/reordenar`, { items_ids: itemIds });
  },

  /**
   * Lista tipos de items que podem ser adicionados
   */
  async listItemTipos(propostaId: string): Promise<{ tipos: ItemTipo[] }> {
    return apiClient.get(`/propostas/${propostaId}/items/tipos`);
  },

  /**
   * Lista mão de obra disponível na base de custos
   */
  async listMaoObra(propostaId: string): Promise<BcuItem[]> {
    return apiClient.get(`/propostas/${propostaId}/items/bcu/mao-obra`);
  },

  /**
   * Lista EPI disponível na base de custos
   */
  async listEpi(propostaId: string): Promise<BcuItem[]> {
    return apiClient.get(`/propostas/${propostaId}/items/bcu/epi`);
  },

  /**
   * Lista equipamentos disponíveis na base de custos
   */
  async listEquipamento(propostaId: string): Promise<BcuItem[]> {
    return apiClient.get(`/propostas/${propostaId}/items/bcu/equipamento`);
  },

  /**
   * Lista ferramentas disponíveis na base de custos
   */
  async listFerramenta(propostaId: string): Promise<BcuItem[]> {
    return apiClient.get(`/propostas/${propostaId}/items/bcu/ferramenta`);
  },

  /**
   * Adiciona mão de obra da base BCU
   */
  async addMaoObra(propostaId: string, body: AddBcuItemRequest): Promise<ProposalItem> {
    return apiClient.post(`/propostas/${propostaId}/items/mao-obra`, body);
  },

  /**
   * Adiciona EPI da base BCU
   */
  async addEpi(propostaId: string, body: AddBcuItemRequest): Promise<ProposalItem> {
    return apiClient.post(`/propostas/${propostaId}/items/epi`, body);
  },

  /**
   * Adiciona equipamento da base BCU
   */
  async addEquipamento(propostaId: string, body: AddBcuItemRequest): Promise<ProposalItem> {
    return apiClient.post(`/propostas/${propostaId}/items/equipamento`, body);
  },

  /**
   * Adiciona ferramenta da base BCU
   */
  async addFerramenta(propostaId: string, body: AddBcuItemRequest): Promise<ProposalItem> {
    return apiClient.post(`/propostas/${propostaId}/items/ferramenta`, body);
  },
};

