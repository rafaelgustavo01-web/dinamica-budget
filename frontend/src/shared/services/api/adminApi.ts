import type { ComputeEmbeddingsResponse } from '../../types/contracts/admin';
import { apiClient } from './apiClient';

export const adminApi = {
  async computeEmbeddings() {
    const response = await apiClient.post<ComputeEmbeddingsResponse>(
      '/admin/compute-embeddings',
    );
    return response.data;
  },
};
