export interface ComputeEmbeddingsResponse {
  status: string;
  embeddings_computados: number;
}

<<<<<<< HEAD
// ── ETL ────────────────────────────────────────────────────────────────────────

export type EtlMode = 'upsert' | 'replace';

export interface EtlItemPreview {
  codigo_origem: string;
  descricao: string;
  unidade_medida: string;
  custo_base: number;
  tipo_recurso: string | null;
}

export interface EtlRelacaoPreview {
  pai_codigo: string;
  filho_codigo: string;
  quantidade_consumo: number;
  unidade_medida: string;
}

export interface EtlParsePreview {
  total_itens: number;
  total_relacoes: number;
  itens_amostra: EtlItemPreview[];
  relacoes_amostra: EtlRelacaoPreview[];
  avisos: string[];
}

export interface EtlUploadResponse {
  arquivo: string;
  parse_preview: EtlParsePreview;
  parse_token: string;
}

export interface EtlExecuteRequest {
  parse_token_tcpo?: string;
  parse_token_converter?: string;
  mode?: EtlMode;
  recomputar_embeddings?: boolean;
}

export interface EtlExecuteResponse {
  mode: EtlMode;
  itens_inseridos: number;
  itens_atualizados: number;
  relacoes_inseridas: number;
  embeddings_computados: number;
  duracao_segundos: number;
  avisos: string[];
}

export interface EtlStatusResponse {
  total_itens_base_tcpo: number;
  total_composicoes_base: number;
  total_embeddings: number;
  ultima_carga: string | null;
=======
export type ImportSourceType = 'TCPO' | 'PC';

export interface FieldMappingPreview {
  source_header: string;
  target_field: string;
  confidence: number;
}

export interface SheetPreview {
  sheet_name: string;
  total_rows: number;
  header_row: number;
  estimated_records: number;
  mapped_fields: FieldMappingPreview[];
  sample_rows: string[][];
}

export interface ImportPreviewResponse {
  source_type: ImportSourceType;
  file_name: string;
  total_rows: number;
  estimated_records: number;
  warnings: string[];
  sheets: SheetPreview[];
}

export interface ImportExecuteResponse {
  status: string;
  source_type: ImportSourceType;
  file_name: string;
  message: string;
  log_excerpt?: string | null;
>>>>>>> 5f0973541797732f99516ee792729f7f3cef10c2
}
