import type { DecimalValue } from './common';

export type TipoRecurso = 'MO' | 'INSUMO' | 'FERRAMENTA' | 'EQUIPAMENTO' | 'SERVICO';

export interface ServicoTcpoResponse {
  id: string;
  codigo_origem: string;
  descricao: string;
  unidade_medida: string;
  custo_unitario: DecimalValue;
  categoria_id: number | null;
  origem: 'TCPO' | 'PROPRIA';
  cliente_id: string | null;
  tipo_recurso: TipoRecurso | null;
  descricao_tokens: string | null;
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

export interface VersaoInfo {
  versao_id: string;
  numero_versao: number;
  origem: 'TCPO' | 'PROPRIA';
  cliente_id: string | null;
}

export interface ExplodeComposicaoResponse {
  servico: ServicoTcpoResponse;
  itens: ComposicaoItemResponse[];
  custo_total_composicao: DecimalValue;
  versao_info: VersaoInfo | null;
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
