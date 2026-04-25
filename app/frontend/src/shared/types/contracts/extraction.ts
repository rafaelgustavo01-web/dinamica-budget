import type { PaginatedResponse } from './common';
import type { TipoRecurso } from './servicos';

export interface ServicoClienteAssociado {
  id: string;               // associacao_inteligente.id
  item_referencia_id: string; // base_tcpo.id — use for BOM explosion
  descricao_cliente: string;  // texto_busca_normalizado (client's own terminology)
  frequencia_uso: number;
  codigo_origem: string;
  descricao_tcpo: string;
  unidade_medida: string;
  custo_base: number;
  tipo_recurso: TipoRecurso | null;
}

export interface ServicosClienteParams {
  cliente_id: string;
  q?: string;
  page?: number;
  page_size?: number;
}

export type ServicosClienteResponse = PaginatedResponse<ServicoClienteAssociado>;
