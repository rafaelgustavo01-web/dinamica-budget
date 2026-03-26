import type { DecimalValue } from './common';

export interface ServicoTcpoResponse {
  id: string;
  codigo_origem: string;
  descricao: string;
  unidade_medida: string;
  custo_unitario: DecimalValue;
  categoria_id: number | null;
}

export interface ComposicaoItemResponse {
  id: string;
  insumo_filho_id: string;
  descricao_filho: string;
  unidade_medida: string;
  quantidade_consumo: DecimalValue;
  custo_unitario: DecimalValue;
  custo_total: DecimalValue;
}

export interface ExplodeComposicaoResponse {
  servico: ServicoTcpoResponse;
  itens: ComposicaoItemResponse[];
  custo_total_composicao: DecimalValue;
}

export interface ServicoCreate {
  codigo_origem: string;
  descricao: string;
  unidade_medida: string;
  custo_unitario: DecimalValue;
  categoria_id?: number | null;
}

export interface ServicoListParams {
  q?: string;
  categoria_id?: number;
  cliente_id?: string;
  page: number;
  page_size: number;
}
