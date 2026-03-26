export type OrigemMatch =
  | 'ASSOCIACAO_DIRETA'
  | 'FUZZY'
  | 'IA_SEMANTICA'
  | 'PROPRIA_CLIENTE';

export interface BuscaServicoRequest {
  cliente_id: string;
  texto_busca: string;
  limite_resultados: number;
  threshold_score: number;
}

export interface ResultadoBusca {
  id_tcpo: string;
  codigo_origem: string;
  descricao: string;
  unidade: string;
  custo_unitario: number;
  score: number;
  score_confianca: number;
  origem_match: OrigemMatch;
  status_homologacao: string;
}

export interface BuscaServicoResponse {
  texto_buscado: string;
  resultados: ResultadoBusca[];
  metadados: {
    tempo_processamento_ms?: number;
    id_historico_busca?: string;
  };
}

export interface CriarAssociacaoRequest {
  cliente_id: string;
  texto_busca_original: string;
  id_tcpo_selecionado: string;
  id_historico_busca: string;
}

export interface AssociacaoResponse {
  status: string;
  mensagem: string;
  id_associacao: string;
}
