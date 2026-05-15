import { apiClient } from './apiClient';

export type RowClass = 'ITEM' | 'SECAO' | 'TOTAL' | 'VAZIA';
export type SmartImportStatus = 'PENDING' | 'REVIEW_REQUIRED' | 'COMPLETED';

export interface StagingRow {
  idx: number;
  sheet_row: number | null;
  row_class: RowClass;
  codigo: string | null;
  descricao: string | null;
  unidade: string | null;
  quantidade: string | null;
  preco: string | null;
  valor: string | null;
}

export interface SmartImportJob {
  id: string;
  cliente_id: string;
  proposta_id: string | null;
  arquivo_origem: string;
  status: SmartImportStatus;
  detected_header_row: number | null;
  detected_data_range: Record<string, unknown> | null;
  mapping_metadata: Record<string, unknown> | null;
  has_warnings: boolean;
  warnings: string[];
  rows: StagingRow[];
}

export interface CommitJobResponse {
  job_id: string;
  status: SmartImportStatus;
  profile_id: string;
  score_confianca: number;
  uso_count: number;
  corrections_applied: number;
}

export interface CorrectionEntry {
  tipo: 'COLUMN_REMAP' | 'HEADER_ROW_FIX' | 'ROW_RECLASSIFY' | 'SHEET_CHANGE';
  detalhe: Record<string, unknown>;
}

export type RowPatch = Partial<
  Pick<StagingRow, 'codigo' | 'descricao' | 'unidade' | 'quantidade' | 'preco' | 'valor'>
>;

export const smartImportApi = {
  upload: (params: {
    file: File;
    cliente_id: string;
    proposta_id?: string;
  }): Promise<SmartImportJob> => {
    const fd = new FormData();
    fd.append('file', params.file);
    fd.append('cliente_id', params.cliente_id);
    if (params.proposta_id) fd.append('proposta_id', params.proposta_id);
    return apiClient.post<SmartImportJob>('/smart-import', fd).then((r) => r.data);
  },

  getJob: (jobId: string): Promise<SmartImportJob> =>
    apiClient.get<SmartImportJob>(`/smart-import/${jobId}`).then((r) => r.data),

  editRow: (jobId: string, rowIdx: number, patch: RowPatch): Promise<StagingRow> =>
    apiClient
      .patch<StagingRow>(`/smart-import/${jobId}/rows/${rowIdx}`, patch)
      .then((r) => r.data),

  addRow: (
    jobId: string,
    data: Omit<StagingRow, 'idx' | 'sheet_row' | 'row_class'> & { descricao: string },
  ): Promise<StagingRow> =>
    apiClient.post<StagingRow>(`/smart-import/${jobId}/rows`, data).then((r) => r.data),

  deleteRow: (jobId: string, rowIdx: number): Promise<void> =>
    apiClient.delete(`/smart-import/${jobId}/rows/${rowIdx}`).then(() => undefined),

  classifyRow: (jobId: string, rowIdx: number, row_class: RowClass): Promise<StagingRow> =>
    apiClient
      .patch<StagingRow>(`/smart-import/${jobId}/rows/${rowIdx}/classify`, { row_class })
      .then((r) => r.data),

  commitJob: (jobId: string, corrections: CorrectionEntry[]): Promise<CommitJobResponse> =>
    apiClient
      .post<CommitJobResponse>(`/smart-import/${jobId}/commit`, { corrections })
      .then((r) => r.data),
};
