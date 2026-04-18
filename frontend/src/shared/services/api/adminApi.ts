import type {
  ComputeEmbeddingsResponse,
  ImportExecuteResponse,
  ImportPreviewResponse,
  ImportSourceType,
} from '../../types/contracts/admin';
import { apiClient } from './apiClient';

export const adminApi = {
  async computeEmbeddings() {
    const response = await apiClient.post<ComputeEmbeddingsResponse>(
      '/admin/compute-embeddings',
    );
    return response.data;
  },

  async previewImport(file: File, sourceType: ImportSourceType) {
    const formData = new FormData();
    formData.append('source_type', sourceType);
    formData.append('file', file);

    const response = await apiClient.post<ImportPreviewResponse>(
      '/admin/import/preview',
      formData,
    );
    return response.data;
  },

  async executeImport(file: File, sourceType: ImportSourceType, confirm = true) {
    const formData = new FormData();
    formData.append('source_type', sourceType);
    formData.append('confirm', String(confirm));
    formData.append('file', file);

    const response = await apiClient.post<ImportExecuteResponse>(
      '/admin/import/execute',
      formData,
    );
    return response.data;
  },
};
