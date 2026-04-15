import type { PaginatedResponse } from '../../types/contracts/common';
import type { UsuarioCreate } from '../../types/contracts/auth';
import type {
  SetPerfisClienteRequest,
  UsuarioAdminResponse,
  UsuarioListParams,
  UsuarioPatchRequest,
  UsuarioPerfisResponse,
} from '../../types/contracts/usuarios';
import { apiClient } from './apiClient';
import { authApi } from './authApi';

export const userApi = {
  async create(payload: UsuarioCreate) {
    return authApi.createUsuario(payload);
  },

  async list(params: UsuarioListParams) {
    const response = await apiClient.get<PaginatedResponse<UsuarioAdminResponse>>('/usuarios/', {
      params,
    });
    return response.data;
  },

  async update(usuarioId: string, payload: UsuarioPatchRequest) {
    const response = await apiClient.patch<UsuarioAdminResponse>(
      `/usuarios/${usuarioId}`,
      payload,
    );
    return response.data;
  },

  async getPerfis(usuarioId: string) {
    const response = await apiClient.get<UsuarioPerfisResponse>(
      `/usuarios/${usuarioId}/perfis-cliente`,
    );
    return response.data;
  },

  async setPerfis(usuarioId: string, payload: SetPerfisClienteRequest) {
    const response = await apiClient.put<UsuarioPerfisResponse>(
      `/usuarios/${usuarioId}/perfis-cliente`,
      payload,
    );
    return response.data;
  },
};
