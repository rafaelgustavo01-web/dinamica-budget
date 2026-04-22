import type {
  ComputeEmbeddingsResponse,
<<<<<<< HEAD
  EtlExecuteRequest,
  EtlExecuteResponse,
  EtlStatusResponse,
  EtlUploadResponse,
=======
  ImportExecuteResponse,
  ImportPreviewResponse,
  ImportSourceType,
>>>>>>> 5f0973541797732f99516ee792729f7f3cef10c2
} from '../../types/contracts/admin';
import { apiClient } from './apiClient';

export const adminApi = {
  async computeEmbeddings() {
    const response = await apiClient.post<ComputeEmbeddingsResponse>(
      '/admin/compute-embeddings',
    );
    return response.data;
  },

<<<<<<< HEAD
  async uploadTcpo(file: File): Promise<EtlUploadResponse> {
    const form = new FormData();
    form.append('file', file);
    const response = await apiClient.post<EtlUploadResponse>(
      '/admin/etl/upload-tcpo',
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } },
=======
  async previewImport(file: File, sourceType: ImportSourceType) {
    const formData = new FormData();
    formData.append('source_type', sourceType);
    formData.append('file', file);

    const response = await apiClient.post<ImportPreviewResponse>(
      '/admin/import/preview',
      formData,
>>>>>>> 5f0973541797732f99516ee792729f7f3cef10c2
    );
    return response.data;
  },

<<<<<<< HEAD
  async uploadConverter(file: File): Promise<EtlUploadResponse> {
    const form = new FormData();
    form.append('file', file);
    const response = await apiClient.post<EtlUploadResponse>(
      '/admin/etl/upload-converter',
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    return response.data;
  },

  async executeEtl(req: EtlExecuteRequest): Promise<EtlExecuteResponse> {
    const response = await apiClient.post<EtlExecuteResponse>(
      '/admin/etl/execute',
      req,
    );
    return response.data;
  },

  async getEtlStatus(): Promise<EtlStatusResponse> {
    const response = await apiClient.get<EtlStatusResponse>('/admin/etl/status');
    return response.data;
  },
=======
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
>>>>>>> 5f0973541797732f99516ee792729f7f3cef10c2
};
