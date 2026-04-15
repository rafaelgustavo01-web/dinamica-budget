export type PerfilUsuario = 'USUARIO' | 'APROVADOR' | 'ADMIN' | string;

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface UsuarioCreate {
  nome: string;
  email: string;
  password: string;
  is_admin: boolean;
}

export interface UsuarioResponse {
  id: string;
  nome: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
}

export interface PerfilClienteResponse {
  cliente_id: string;
  perfil: PerfilUsuario;
}

export interface MeResponse extends UsuarioResponse {
  perfis: PerfilClienteResponse[];
}

export interface ProfileUpdateRequest {
  nome: string;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}
