export interface ComputeEmbeddingsResponse {
  status: string;
  embeddings_computados: number;
}

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
}
