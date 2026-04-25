import type { ExplodeComposicaoResponse } from '../../types/contracts/servicos';
import type {
  ServicosClienteParams,
  ServicosClienteResponse,
} from '../../types/contracts/extraction';
import { apiClient } from './apiClient';

export const extractionApi = {
  async getServicosCliente(
    params: ServicosClienteParams,
  ): Promise<ServicosClienteResponse> {
    const response = await apiClient.get<ServicosClienteResponse>(
      '/extracao/servicos-cliente',
      { params },
    );
    return response.data;
  },

  async getDadosBrutos(
    servicoId: string,
    clienteId: string,
  ): Promise<ExplodeComposicaoResponse> {
    const response = await apiClient.get<ExplodeComposicaoResponse>(
      `/extracao/${servicoId}/dados-brutos`,
      { params: { cliente_id: clienteId } },
    );
    return response.data;
  },

  async downloadXlsx(servicoId: string, clienteId: string): Promise<void> {
    const response = await apiClient.get(
      `/extracao/${servicoId}/download-xlsx`,
      {
        params: { cliente_id: clienteId },
        responseType: 'blob',
      },
    );
    const disposition: string =
      response.headers['content-disposition'] ?? '';
    const match = disposition.match(/filename="([^"]+)"/);
    const filename = match ? match[1] : `PC_${servicoId}.xlsx`;

    const url = URL.createObjectURL(new Blob([response.data as BlobPart]));
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  },
};
