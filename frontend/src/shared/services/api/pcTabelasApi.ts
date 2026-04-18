import { apiClient } from './apiClient';

export interface PcCabecalho {
  id: string;
  nome_arquivo: string;
  data_referencia: string | null;
  versao_layout: string | null;
  observacao: string | null;
  criado_em: string;
}

export interface PcMaoObraItem {
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

export interface PcEquipamentoPremissa {
  id: string;
  horas_mes: number | null;
  preco_gasolina_l: number | null;
  preco_diesel_l: number | null;
}

export interface PcEquipamentoItem {
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

export interface PcEquipamentosOut {
  premissa: PcEquipamentoPremissa | null;
  items: PcEquipamentoItem[];
}

export interface PcEncargoItem {
  id: string;
  tipo_encargo: string;
  grupo: string | null;
  codigo_grupo: string | null;
  discriminacao_encargo: string;
  taxa_percent: number | null;
}

export interface PcEpiItem {
  id: string;
  epi: string;
  unidade: string | null;
  custo_unitario: number | null;
  quantidade: number | null;
  vida_util_meses: number | null;
  custo_epi_mes: number | null;
}

export interface PcFerramentaItem {
  id: string;
  item: string | null;
  descricao: string;
  unidade: string | null;
  quantidade: number | null;
  preco: number | null;
  preco_total: number | null;
}

export interface PcMobilizacaoQuantidadeFuncao {
  coluna_funcao: string;
  quantidade: number | null;
}

export interface PcMobilizacaoItem {
  id: string;
  descricao: string;
  funcao: string | null;
  tipo_mao_obra: string | null;
  quantidades_funcao: PcMobilizacaoQuantidadeFuncao[];
}

export const pcTabelasApi = {
  async listCabecalhos(): Promise<PcCabecalho[]> {
    const r = await apiClient.get<PcCabecalho[]>('/pc-tabelas/cabecalhos');
    return r.data;
  },

  async getMaoObra(cabecalhoId: string): Promise<PcMaoObraItem[]> {
    const r = await apiClient.get<PcMaoObraItem[]>(`/pc-tabelas/${cabecalhoId}/mao-obra`);
    return r.data;
  },

  async getEquipamentos(cabecalhoId: string): Promise<PcEquipamentosOut> {
    const r = await apiClient.get<PcEquipamentosOut>(`/pc-tabelas/${cabecalhoId}/equipamentos`);
    return r.data;
  },

  async getEncargos(cabecalhoId: string, tipo?: string): Promise<PcEncargoItem[]> {
    const params = tipo ? { tipo } : undefined;
    const r = await apiClient.get<PcEncargoItem[]>(`/pc-tabelas/${cabecalhoId}/encargos`, { params });
    return r.data;
  },

  async getEpi(cabecalhoId: string): Promise<PcEpiItem[]> {
    const r = await apiClient.get<PcEpiItem[]>(`/pc-tabelas/${cabecalhoId}/epi`);
    return r.data;
  },

  async getFerramentas(cabecalhoId: string): Promise<PcFerramentaItem[]> {
    const r = await apiClient.get<PcFerramentaItem[]>(`/pc-tabelas/${cabecalhoId}/ferramentas`);
    return r.data;
  },

  async getMobilizacao(cabecalhoId: string): Promise<PcMobilizacaoItem[]> {
    const r = await apiClient.get<PcMobilizacaoItem[]>(`/pc-tabelas/${cabecalhoId}/mobilizacao`);
    return r.data;
  },

  async importarPlanilha(file: File): Promise<PcCabecalho> {
    const formData = new FormData();
    formData.append('file', file);
    const r = await apiClient.post<PcCabecalho>('/pc-tabelas/importar', formData);
    return r.data;
  },
};
