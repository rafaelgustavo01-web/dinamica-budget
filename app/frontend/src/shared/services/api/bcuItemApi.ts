import { apiClient } from './apiClient';

// ── Upload Individual ─────────────────────────────────────────────────────────

export type BcuTableType = 'MO' | 'EQP' | 'ENC' | 'EXM' | 'EPI' | 'FER' | 'MOB';

export interface BcuUploadIndividualResponse {
  cabecalho_id: string;
  tabela: BcuTableType;
  linhas_inseridas: number;
  linhas_atualizadas: number;
  erros: BcuUploadError[];
  observacao: string | null;
}

export interface BcuUploadError {
  linha: number;
  campo: string;
  valor: string | null;
  mensagem: string;
}

export interface BcuUploadIndividualPayload {
  file: File;
  cabecalho_id: string;
  tabela: BcuTableType;
  modo: 'upsert' | 'append';
}

// ── CRUD: Mão de Obra ───────────────────────────────────────────────────────

export interface BcuMaoObraItemCreate {
  descricao_funcao: string;
  codigo_origem?: string | null;
  salario?: number | null;
  previsao_reajuste?: number | null;
  encargos_percent?: number | null;
  periculosidade_insalubridade?: number | null;
  refeicao?: number | null;
  agua_potavel?: number | null;
  vale_alimentacao?: number | null;
  plano_saude?: number | null;
  ferramentas_val?: number | null;
  seguro_vida?: number | null;
  abono_ferias?: number | null;
  uniforme_val?: number | null;
  epi_val?: number | null;
  custo_unitario_h?: number | null;
  custo_mensal?: number | null;
  mobilizacao?: number | null;
}

export interface BcuMaoObraItemUpdate extends Partial<BcuMaoObraItemCreate> {}

// ── CRUD: Equipamentos ────────────────────────────────────────────────────────

export interface BcuEquipamentoItemCreate {
  codigo?: string | null;
  codigo_origem?: string | null;
  equipamento: string;
  combustivel_utilizado?: string | null;
  consumo_l_h?: number | null;
  aluguel_r_h?: number | null;
  combustivel_r_h?: number | null;
  mao_obra_r_h?: number | null;
  hora_produtiva?: number | null;
  hora_improdutiva?: number | null;
  mes?: number | null;
  aluguel_mensal?: number | null;
}

export interface BcuEquipamentoItemUpdate extends Partial<BcuEquipamentoItemCreate> {}

export interface BcuEquipamentoPremissaUpdate {
  horas_mes?: number | null;
  preco_gasolina_l?: number | null;
  preco_diesel_l?: number | null;
}

// ── CRUD: Encargos ────────────────────────────────────────────────────────────

export interface BcuEncargoItemCreate {
  tipo_encargo: 'HORISTA' | 'MENSALISTA';
  grupo?: string | null;
  codigo_grupo?: string | null;
  discriminacao_encargo: string;
  taxa_percent?: number | null;
}

export interface BcuEncargoItemUpdate extends Partial<BcuEncargoItemCreate> {}

// ── CRUD: EPI ─────────────────────────────────────────────────────────────────

export interface BcuEpiItemCreate {
  codigo_origem?: string | null;
  epi: string;
  unidade?: string | null;
  custo_unitario?: number | null;
  vida_util_meses?: number | null;
  custo_epi_mes?: number | null;
}

export interface BcuEpiItemUpdate extends Partial<BcuEpiItemCreate> {}

// ── CRUD: Ferramentas ─────────────────────────────────────────────────────────

export interface BcuFerramentaItemCreate {
  codigo_origem?: string | null;
  item?: string | null;
  descricao: string;
  unidade?: string | null;
  preco?: number | null;
  preco_total?: number | null;
}

export interface BcuFerramentaItemUpdate extends Partial<BcuFerramentaItemCreate> {}

// ── CRUD: Mobilização ─────────────────────────────────────────────────────────

export interface BcuMobilizacaoQuantidadeFuncaoCreate {
  coluna_funcao: string;
  quantidade?: number | null;
}

export interface BcuMobilizacaoItemCreate {
  descricao: string;
  funcao?: string | null;
  tipo_mao_obra?: string | null;
  quantidades_funcao: BcuMobilizacaoQuantidadeFuncaoCreate[];
}

export interface BcuMobilizacaoItemUpdate extends Partial<Omit<BcuMobilizacaoItemCreate, 'quantidades_funcao'>> {
  quantidades_funcao?: BcuMobilizacaoQuantidadeFuncaoCreate[];
}

// ── API ───────────────────────────────────────────────────────────────────────

export const bcuItemApi = {
  // Upload individual por tabela
  async uploadIndividual(payload: BcuUploadIndividualPayload): Promise<BcuUploadIndividualResponse> {
    const formData = new FormData();
    formData.append('file', payload.file);
    const tipoMap: Record<BcuTableType, string> = {
      MO: 'mo',
      EQP: 'equipamentos',
      ENC: 'encargos',
      EXM: 'exames',
      EPI: 'epi',
      FER: 'ferramentas',
      MOB: 'mobilizacao',
    };
    const tipo = tipoMap[payload.tabela];
    const r = await apiClient.post<{ tipo: string; cabecalho_id: string; imported_rows: number; warnings: string[] | null }>(
      '/bcu/upload-individual/' + tipo + '/confirmar',
      formData,
      { params: { cabecalho_id: payload.cabecalho_id } },
    );
    return {
      cabecalho_id: r.data.cabecalho_id,
      tabela: payload.tabela,
      linhas_inseridas: r.data.imported_rows,
      linhas_atualizadas: 0,
      erros: (r.data.warnings ?? []).map((mensagem, idx) => ({ linha: idx + 1, campo: 'arquivo', valor: null, mensagem })),
      observacao: null,
    };
  },

  // ── Mão de Obra ────────────────────────────────────────────────────────────
  async criarMaoObra(cabecalhoId: string, body: BcuMaoObraItemCreate) {
    const r = await apiClient.post<{ id: string }>(`/bcu/${cabecalhoId}/mao-obra`, body);
    return r.data;
  },
  async atualizarMaoObra(cabecalhoId: string, itemId: string, body: BcuMaoObraItemUpdate) {
    await apiClient.patch(`/bcu/${cabecalhoId}/mao-obra/${itemId}`, body);
  },
  async deletarMaoObra(cabecalhoId: string, itemId: string) {
    await apiClient.delete(`/bcu/${cabecalhoId}/mao-obra/${itemId}`);
  },

  // ── Equipamentos ───────────────────────────────────────────────────────────
  async criarEquipamento(cabecalhoId: string, body: BcuEquipamentoItemCreate) {
    const r = await apiClient.post<{ id: string }>(`/bcu/${cabecalhoId}/equipamentos`, body);
    return r.data;
  },
  async atualizarEquipamento(cabecalhoId: string, itemId: string, body: BcuEquipamentoItemUpdate) {
    await apiClient.patch(`/bcu/${cabecalhoId}/equipamentos/${itemId}`, body);
  },
  async deletarEquipamento(cabecalhoId: string, itemId: string) {
    await apiClient.delete(`/bcu/${cabecalhoId}/equipamentos/${itemId}`);
  },
  async atualizarEquipamentoPremissa(cabecalhoId: string, body: BcuEquipamentoPremissaUpdate) {
    await apiClient.patch(`/bcu/${cabecalhoId}/equipamentos/premissa`, body);
  },

  // ── Encargos ───────────────────────────────────────────────────────────────
  async criarEncargo(cabecalhoId: string, body: BcuEncargoItemCreate) {
    const r = await apiClient.post<{ id: string }>(`/bcu/${cabecalhoId}/encargos`, body);
    return r.data;
  },
  async atualizarEncargo(cabecalhoId: string, itemId: string, body: BcuEncargoItemUpdate) {
    await apiClient.patch(`/bcu/${cabecalhoId}/encargos/${itemId}`, body);
  },
  async deletarEncargo(cabecalhoId: string, itemId: string) {
    await apiClient.delete(`/bcu/${cabecalhoId}/encargos/${itemId}`);
  },

  // ── EPI ────────────────────────────────────────────────────────────────────
  async criarEpi(cabecalhoId: string, body: BcuEpiItemCreate) {
    const r = await apiClient.post<{ id: string }>(`/bcu/${cabecalhoId}/epi`, body);
    return r.data;
  },
  async atualizarEpi(cabecalhoId: string, itemId: string, body: BcuEpiItemUpdate) {
    await apiClient.patch(`/bcu/${cabecalhoId}/epi/${itemId}`, body);
  },
  async deletarEpi(cabecalhoId: string, itemId: string) {
    await apiClient.delete(`/bcu/${cabecalhoId}/epi/${itemId}`);
  },

  // ── Ferramentas ────────────────────────────────────────────────────────────
  async criarFerramenta(cabecalhoId: string, body: BcuFerramentaItemCreate) {
    const r = await apiClient.post<{ id: string }>(`/bcu/${cabecalhoId}/ferramentas`, body);
    return r.data;
  },
  async atualizarFerramenta(cabecalhoId: string, itemId: string, body: BcuFerramentaItemUpdate) {
    await apiClient.patch(`/bcu/${cabecalhoId}/ferramentas/${itemId}`, body);
  },
  async deletarFerramenta(cabecalhoId: string, itemId: string) {
    await apiClient.delete(`/bcu/${cabecalhoId}/ferramentas/${itemId}`);
  },

  // ── Mobilização ────────────────────────────────────────────────────────────
  async criarMobilizacao(cabecalhoId: string, body: BcuMobilizacaoItemCreate) {
    const r = await apiClient.post<{ id: string }>(`/bcu/${cabecalhoId}/mobilizacao`, body);
    return r.data;
  },
  async atualizarMobilizacao(cabecalhoId: string, itemId: string, body: BcuMobilizacaoItemUpdate) {
    await apiClient.patch(`/bcu/${cabecalhoId}/mobilizacao/${itemId}`, body);
  },
  async deletarMobilizacao(cabecalhoId: string, itemId: string) {
    await apiClient.delete(`/bcu/${cabecalhoId}/mobilizacao/${itemId}`);
  },
};
