import type { PaginatedResponse } from './common';
import type { DecimalValue } from './common';
import type { ServicoTcpoResponse } from './servicos';

export interface ItemPendenteResponse {
  id: string;
  codigo_origem: string;
  descricao: string;
  unidade_medida: string;
  custo_unitario: DecimalValue;
  cliente_id: string;
  origem: string;
  status_homologacao: string;
  created_at: string;
}

export interface AprovarHomologacaoRequest {
  servico_id: string;
  cliente_id: string;
  aprovado: boolean;
  motivo_reprovacao?: string | null;
}

export interface AprovarHomologacaoResponse {
  servico_id: string;
  status_homologacao: string;
  aprovado_por: string;
  data_aprovacao: string;
  mensagem: string;
}

export interface CriarItemProprioRequest {
  cliente_id: string;
  codigo_origem: string;
  descricao: string;
  unidade_medida: string;
  custo_unitario: DecimalValue;
  categoria_id?: number | null;
}

export type PendentesHomologacaoResponse = PaginatedResponse<ItemPendenteResponse>;
export type CriarItemProprioResponse = ServicoTcpoResponse;
