import type { StatusProposta, PropostaResponse } from '../../shared/services/api/proposalsApi';

export type { StatusProposta, PropostaResponse as Proposta };

export interface PropostaFormData {
  titulo: string;
  descricao?: string;
}

export interface PqItem {
  id: string;
  descricao_original: string;
  quantidade_original: number;
  match_status: string;
  match_confidence: number | null;
}

export interface CpuItem {
  id: string;
  codigo: string;
  descricao: string;
  quantidade: number;
  unidade: string;
  preco_unitario: number;
  preco_total: number;
}
