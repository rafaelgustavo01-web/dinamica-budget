export interface VersaoComposicaoResponse {
  id: string;
  numero_versao: number;
  origem: 'TCPO' | 'PROPRIA';
  cliente_id: string | null;
  is_ativa: boolean;
  criado_em: string;
}
