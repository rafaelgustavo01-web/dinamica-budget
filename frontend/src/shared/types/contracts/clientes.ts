export interface ClienteResponse {
  id: string;
  nome_fantasia: string;
  cnpj: string;
  is_active: boolean;
}

export interface ClienteCreateRequest {
  nome_fantasia: string;
  cnpj: string;
}

export interface ClienteListParams {
  is_active?: boolean;
  page: number;
  page_size: number;
}
