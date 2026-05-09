export interface ClienteResponse {
  id: string;
  nome_fantasia: string;
  cnpj: string;
  razao_social?: string | null;
  inscricao_estadual?: string | null;
  inscricao_municipal?: string | null;
  endereco_logradouro?: string | null;
  endereco_numero?: string | null;
  endereco_complemento?: string | null;
  endereco_bairro?: string | null;
  endereco_municipio?: string | null;
  endereco_uf?: string | null;
  endereco_cep?: string | null;
  contato_nome?: string | null;
  contato_email?: string | null;
  contato_telefone?: string | null;
  is_active: boolean;
}

export interface ClienteCreateRequest {
  nome_fantasia: string;
  cnpj: string;
  razao_social?: string | null;
  inscricao_estadual?: string | null;
  inscricao_municipal?: string | null;
  endereco_logradouro?: string | null;
  endereco_numero?: string | null;
  endereco_complemento?: string | null;
  endereco_bairro?: string | null;
  endereco_municipio?: string | null;
  endereco_uf?: string | null;
  endereco_cep?: string | null;
  contato_nome?: string | null;
  contato_email?: string | null;
  contato_telefone?: string | null;
}

export interface ClientePatchRequest {
  nome_fantasia?: string;
  razao_social?: string | null;
  inscricao_estadual?: string | null;
  inscricao_municipal?: string | null;
  endereco_logradouro?: string | null;
  endereco_numero?: string | null;
  endereco_complemento?: string | null;
  endereco_bairro?: string | null;
  endereco_municipio?: string | null;
  endereco_uf?: string | null;
  endereco_cep?: string | null;
  contato_nome?: string | null;
  contato_email?: string | null;
  contato_telefone?: string | null;
  is_active?: boolean;
}

export interface ClienteListParams {
  is_active?: boolean;
  nome?: string;
  page: number;
  page_size: number;
}
