import type {
  LoginRequest,
  MeResponse,
  PasswordChangeRequest,
  ProfileUpdateRequest,
  TokenResponse,
  UsuarioCreate,
  UsuarioResponse,
} from '../../types/contracts/auth';
import { apiClient, publicApiClient } from './apiClient';

export const authApi = {
  async login(payload: LoginRequest) {
    const response = await publicApiClient.post<TokenResponse>('/auth/login', payload);
    return response.data;
  },

  async refresh(refreshToken: string) {
    const response = await publicApiClient.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  async getMe() {
    const response = await apiClient.get<MeResponse>('/auth/me');
    return response.data;
  },

  async logout() {
    await apiClient.post('/auth/logout');
  },

  async createUsuario(payload: UsuarioCreate) {
    const response = await apiClient.post<UsuarioResponse>('/auth/usuarios', payload);
    return response.data;
  },

  async updateProfile(payload: ProfileUpdateRequest) {
    const response = await apiClient.patch<MeResponse>('/auth/me', payload);
    return response.data;
  },

  async changePassword(payload: PasswordChangeRequest) {
    await apiClient.post('/auth/trocar-senha', payload);
  },
};
