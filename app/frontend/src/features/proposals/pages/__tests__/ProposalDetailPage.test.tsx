import { describe, it, expect, vi } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { server } from '../../../../test/msw/server';
import { renderWithProviders } from '../../../../test/test-utils';
import { ProposalDetailPage } from '../ProposalDetailPage';

vi.mock('../../../auth/AuthProvider', () => ({
  useAuth: () => ({
    user: { id: 'u1', nome: 'Admin', is_admin: true, perfil: 'ADMIN' },
    isAuthenticated: true,
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
}));

const mockProposta = {
  id: 'p1',
  cliente_id: 'client-1',
  criado_por_id: 'u1',
  codigo: 'PROP-2026-001',
  titulo: 'Obra Alpha',
  descricao: 'Descrição da obra alpha',
  status: 'CPU_GERADA',
  versao_cpu: 1,
  bcu_cabecalho_id: 'bcu-1',
  total_direto: 150000,
  total_indireto: 30000,
  total_geral: 180000,
  data_finalizacao: null,
  created_at: '2026-04-20T10:00:00Z',
  updated_at: '2026-04-20T10:00:00Z',
  meu_papel: 'OWNER',
  proposta_root_id: 'root-1',
  numero_versao: 1,
  versao_anterior_id: null,
  is_versao_atual: true,
  is_fechada: false,
  requer_aprovacao: true,
  aprovado_por_id: null,
  aprovado_em: null,
  motivo_revisao: null,
  cpu_desatualizada: false,
};

function setupCommonHandlers() {
  server.use(
    http.get('/api/v1/propostas/root/root-1/versoes', () => {
      return HttpResponse.json([]);
    }),
  );
}

describe('ProposalDetailPage', () => {
  it('renderiza header da proposta + abas', async () => {
    setupCommonHandlers();
    server.use(
      http.get('/api/v1/propostas/p1', () => {
        return HttpResponse.json(mockProposta);
      }),
    );

    renderWithProviders(<ProposalDetailPage />, {
      route: '/propostas/p1',
      path: '/propostas/:id',
    });

    expect(await screen.findByText(/Proposta: PROP-2026-001/i)).toBeInTheDocument();
    expect(screen.getByText('Obra Alpha')).toBeInTheDocument();
    expect(screen.getByText('Dados da Proposta')).toBeInTheDocument();
    expect(screen.getByText('Totais')).toBeInTheDocument();
  });

  it('ExportMenu abre com 2 opcoes (Excel, PDF)', async () => {
    setupCommonHandlers();
    server.use(
      http.get('/api/v1/propostas/p1', () => {
        return HttpResponse.json(mockProposta);
      }),
    );

    renderWithProviders(<ProposalDetailPage />, {
      route: '/propostas/p1',
      path: '/propostas/:id',
    });

    await screen.findByText(/Proposta: PROP-2026-001/i);

    const exportBtn = screen.getByRole('button', { name: /Exportar/i });
    fireEvent.click(exportBtn);

    expect(screen.getByText('Excel (xlsx)')).toBeInTheDocument();
    expect(screen.getByText('PDF (folha de rosto)')).toBeInTheDocument();
  });

  it('erro de export exibe Alert/Snackbar', async () => {
    setupCommonHandlers();
    server.use(
      http.get('/api/v1/propostas/p1', () => {
        return HttpResponse.json(mockProposta);
      }),
      http.get('/api/v1/propostas/p1/export/excel', () => {
        return new HttpResponse(null, { status: 500 });
      }),
    );

    renderWithProviders(<ProposalDetailPage />, {
      route: '/propostas/p1',
      path: '/propostas/:id',
    });

    await screen.findByText(/Proposta: PROP-2026-001/i);

    fireEvent.click(screen.getByRole('button', { name: /Exportar/i }));
    fireEvent.click(screen.getByText('Excel (xlsx)'));

    await waitFor(() => {
      expect(screen.getByText('Falha ao exportar Excel. Tente novamente.')).toBeInTheDocument();
    });
  });

  it('botao Excluir esta presente para OWNER', async () => {
    setupCommonHandlers();
    server.use(
      http.get('/api/v1/propostas/p1', () => {
        return HttpResponse.json(mockProposta);
      }),
    );

    renderWithProviders(<ProposalDetailPage />, {
      route: '/propostas/p1',
      path: '/propostas/:id',
    });

    await screen.findByText(/Proposta: PROP-2026-001/i);

    expect(screen.getByRole('button', { name: /Excluir/i })).toBeInTheDocument();
  });
});
