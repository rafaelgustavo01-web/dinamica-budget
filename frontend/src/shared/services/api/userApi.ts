import type { UsuarioCreate } from '../../types/contracts/auth';
import { authApi } from './authApi';

export const userApi = {
  async create(payload: UsuarioCreate) {
    return authApi.createUsuario(payload);
  },
};
