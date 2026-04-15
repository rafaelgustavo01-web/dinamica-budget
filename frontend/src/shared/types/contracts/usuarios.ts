import type { PerfilUsuario } from './auth';

export interface UsuarioAdminResponse {
  id: string;
  nome: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  external_id_ad: string | null;
}

export interface UsuarioListParams {
  is_active?: boolean;
  page: number;
  page_size: number;
}

export interface UsuarioPatchRequest {
  nome?: string;
  email?: string;
  is_active?: boolean;
  is_admin?: boolean;
}

export interface PerfilClienteItem {
  cliente_id: string;
  perfil: PerfilUsuario;
}

export interface UsuarioPerfisResponse {
  usuario_id: string;
  perfis: PerfilClienteItem[];
}

export interface SetPerfisClienteRequest {
  cliente_id: string;
  perfis: PerfilUsuario[];
}
