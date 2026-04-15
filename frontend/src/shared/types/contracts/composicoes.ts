export interface ClonarComposicaoRequest {
  servico_origem_id: string;
  cliente_id: string;
  codigo_clone: string;
  descricao?: string;
}

export interface AdicionarComponenteRequest {
  insumo_filho_id: string;
  quantidade_consumo: number;
  unidade_medida: string;  // unidade do insumo_filho na composição
}
