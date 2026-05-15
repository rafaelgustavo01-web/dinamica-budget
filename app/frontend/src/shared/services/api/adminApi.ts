import type {
  ComputeEmbeddingsResponse,
  EtlExecuteRequest,
  EtlExecuteResponse,
  EtlStatusResponse,
  EtlUploadResponse,
  SystemSettingsResponse,
  SystemSettingsUpdate,
} from '../../types/contracts/admin';
import { apiClient } from './apiClient';

export const adminApi = {
  async computeEmbeddings() {
    const response = await apiClient.post<ComputeEmbeddingsResponse>(
      '/admin/compute-embeddings',
      undefined,
      { timeout: 180000 },
    );
    return response.data;
  },

  // ETL endpoints (DB-backed parse tokens, durable across restarts)
  async uploadTcpo(file: File): Promise<EtlUploadResponse> {
    const form = new FormData();
    form.append('file', file);
    const response = await apiClient.post<EtlUploadResponse>(
      '/admin/etl/upload-tcpo',
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    );
    return response.data;
  },

  async executeEtl(req: EtlExecuteRequest): Promise<EtlExecuteResponse> {
    const response = await apiClient.post<EtlExecuteResponse>(
      '/admin/etl/execute',
      req,
      { timeout: 180000 },
    );
    return response.data;
  },

  async getEtlStatus(): Promise<EtlStatusResponse> {
    const response = await apiClient.get<EtlStatusResponse>('/admin/etl/status');
    return response.data;
  },

  async getSettings(): Promise<SystemSettingsResponse> {
    const response = await apiClient.get<SystemSettingsResponse>('/admin/settings');
    return response.data;
  },

  async updateSettings(payload: SystemSettingsUpdate): Promise<SystemSettingsResponse> {
    const response = await apiClient.patch<SystemSettingsResponse>('/admin/settings', payload);
    return response.data;
  },
};
