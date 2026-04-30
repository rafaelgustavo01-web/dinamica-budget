import { apiClient } from './apiClient';

export interface BcuCabecalho {
  id: string;
  nome_arquivo: string;
  data_referencia: string | null;
  versao_layout: string | null;
  observacao: string | null;
  is_ativo: boolean;
  criado_em: string;
}

export interface BcuMaoObraItem {
  id: string;
  descricao_funcao: string;
  quantidade: number | null;
  salario: number | null;
  previsao_reajuste: number | null;
  encargos_percent: number | null;
  periculosidade_insalubridade: number | null;
  refeicao: number | null;
  agua_potavel: number | null;
  vale_alimentacao: number | null;
  plano_saude: number | null;
  ferramentas_val: number | null;
  seguro_vida: number | null;
  abono_ferias: number | null;
  uniforme_val: number | null;
  epi_val: number | null;
  custo_unitario_h: number | null;
  custo_mensal: number | null;
  mobilizacao: number | null;
}

export interface BcuEquipamentoPremissa {
  id: string;
  horas_mes: number | null;
  preco_gasolina_l: number | null;
  preco_diesel_l: number | null;
}

export interface BcuEquipamentoItem {
  id: string;
  codigo: string | null;
  equipamento: string;
  combustivel_utilizado: string | null;
  consumo_l_h: number | null;
  aluguel_r_h: number | null;
  combustivel_r_h: number | null;
  mao_obra_r_h: number | null;
  hora_produtiva: number | null;
  hora_improdutiva: number | null;
  mes: number | null;
  aluguel_mensal: number | null;
}

export interface BcuEquipamentosOut {
  premissa: BcuEquipamentoPremissa | null;
  items: BcuEquipamentoItem[];
}

export interface BcuEncargoItem {
  id: string;
  tipo_encargo: string;
  grupo: string | null;
  codigo_grupo: string | null;
  discriminacao_encargo: string;
  taxa_percent: number | null;
}

export interface BcuEpiItem {
  id: string;
  epi: string;
  unidade: string | null;
  custo_unitario: number | null;
  quantidade: number | null;
  vida_util_meses: number | null;
  custo_epi_mes: number | null;
}

export interface BcuFerramentaItem {
  id: string;
  item: string | null;
  descricao: string;
  unidade: string | null;
  quantidade: number | null;
  preco: number | null;
  preco_total: number | null;
}

export interface BcuMobilizacaoQuantidadeFuncao {
  coluna_funcao: string;
  quantidade: number | null;
}

export interface BcuMobilizacaoItem {
  id: string;
  descricao: string;
  funcao: string | null;
  tipo_mao_obra: string | null;
  quantidades_funcao: BcuMobilizacaoQuantidadeFuncao[];
}

export const bcuApi = {
  async listCabecalhos(): Promise<BcuCabecalho[]> {
    const r = await apiClient.get<BcuCabecalho[]>('/bcu/cabecalhos');
    return r.data;
  },

  async getCabecalhoAtivo(): Promise<BcuCabecalho | null> {
    const r = await apiClient.get<BcuCabecalho | null>('/bcu/cabecalho-ativo');
    return r.data;
  },

  async getMaoObra(cabecalhoId: string): Promise<BcuMaoObraItem[]> {
    const r = await apiClient.get<BcuMaoObraItem[]>(`/bcu/${cabecalhoId}/mao-obra`);
    return r.data;
  },

  async getEquipamentos(cabecalhoId: string): Promise<BcuEquipamentosOut> {
    const r = await apiClient.get<BcuEquipamentosOut>(`/bcu/${cabecalhoId}/equipamentos`);
    return r.data;
  },

  async getEncargos(cabecalhoId: string, tipo?: string): Promise<BcuEncargoItem[]> {
    const params = tipo ? { tipo } : undefined;
    const r = await apiClient.get<BcuEncargoItem[]>(`/bcu/${cabecalhoId}/encargos`, { params });
    return r.data;
  },

  async getEpi(cabecalhoId: string): Promise<BcuEpiItem[]> {
    const r = await apiClient.get<BcuEpiItem[]>(`/bcu/${cabecalhoId}/epi`);
    return r.data;
  },

  async getFerramentas(cabecalhoId: string): Promise<BcuFerramentaItem[]> {
    const r = await apiClient.get<BcuFerramentaItem[]>(`/bcu/${cabecalhoId}/ferramentas`);
    return r.data;
  },

  async getMobilizacao(cabecalhoId: string): Promise<BcuMobilizacaoItem[]> {
    const r = await apiClient.get<BcuMobilizacaoItem[]>(`/bcu/${cabecalhoId}/mobilizacao`);
    return r.data;
  },

  async importarPlanilha(file: File): Promise<BcuCabecalho> {
    const formData = new FormData();
    formData.append('file', file);
    // Endpoint atualizado: planilha-fonte oficial agora é "Converter em Data Center.xlsx"
    // (6 abas: Mão de Obra, Equipamentos, Encargos, EPI/Uniforme, Ferramentas, Exames).
    const r = await apiClient.post<BcuCabecalho>('/bcu/importar-converter', formData);
    return r.data;
  },

  async ativarCabecalho(cabecalhoId: string): Promise<BcuCabecalho> {
    const r = await apiClient.post<BcuCabecalho>(`/bcu/cabecalhos/${cabecalhoId}/ativar`);
    return r.data;
  },
};
