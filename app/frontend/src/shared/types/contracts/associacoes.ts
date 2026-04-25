import type { DecimalValue } from './common';

export interface AssociacaoListItem {
  id: string;
  cliente_id: string;
  texto_busca_normalizado: string;
  servico_tcpo_id: string;
  origem_associacao: string;
  frequencia_uso: number;
  status_validacao: string;
  confiabilidade_score: DecimalValue | null;
}

export interface AssociacaoListParams {
  cliente_id: string;
  page: number;
  page_size: number;
}
