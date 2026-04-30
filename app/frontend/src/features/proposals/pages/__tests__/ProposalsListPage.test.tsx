import { describe, it, expect, vi } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { server } from '../../../../test/msw/server';
import { renderWithProviders } from '../../../../test/test-utils';
import { ProposalsListPage } from '../ProposalsListPage';
import { useLocation } from 'react-router-dom';

vi.mock('../../../auth/AuthProvider', () => ({
  useAuth: () => ({ selectedClientId: 'client-1', user: null, isAuthenticated: true }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
}));

function LocationCapture() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname}</div>;
}

const mockPropostas = {
  items: [
    {
      id: 'p1',
      cliente_id: 'client-1',
      criado_por_id: 'u1',
      codigo: 'PROP-2026-001',
      titulo: 'Obra Alpha',
      descricao: null,
      status: 'RASCUNHO',
      versao_cpu: 1,
      bcu_cabecalho_id: null,
      total_direto: 150000,
      total_indireto: 30000,
      total_geral: 180000,
      data_finalizacao: null,
      created_at: '2026-04-20T10:00:00Z',
      updated_at: '2026-04-20T10:00:00Z',
      meu_papel: 'OWNER' as const,
      proposta_root_id: null,
      numero_versao: null,
      versao_anterior_id: null,
      is_versao_atual: null,
      is_fechada: null,
      requer_aprovacao: false,
      aprovado_por_id: null,
      aprovado_em: null,
      motivo_revisao: null,
      cpu_desatualizada: false,
    },
    {
      id: 'p2',
      cliente_id: 'client-1',
      criado_por_id: 'u1',
      codigo: 'PROP-2026-002',
      titulo: 'Obra Beta',
      descricao: null,
      status: 'CPU_GERADA',
      versao_cpu: 1,
      bcu_cabecalho_id: null,
      total_direto: 250000,
      total_indireto: 50000,
      total_geral: 300000,
      data_finalizacao: null,
      created_at: '2026-04-21T10:00:00Z',
      updated_at: '2026-04-21T10:00:00Z',
      meu_papel: 'EDITOR' as const,
      proposta_root_id: null,
      numero_versao: null,
      versao_anterior_id: null,
      is_versao_atual: null,
      is_fechada: null,
      requer_aprovacao: false,
      aprovado_por_id: null,
      aprovado_em: null,
      motivo_revisao: null,
      cpu_desatualizada: false,
    },
    {
      id: 'p3',
      cliente_id: 'client-1',
      criado_por_id: 'u1',
      codigo: 'PROP-2026-003',
      titulo: 'Obra Gamma',
      descricao: null,
      status: 'APROVADA',
      versao_cpu: 1,
      bcu_cabecalho_id: null,
      total_direto: null,
      total_indireto: null,
      total_geral: null,
      data_finalizacao: null,
      created_at: '2026-04-22T10:00:00Z',
      updated_at: '2026-04-22T10:00:00Z',
      meu_papel: 'VIEWER' as const,
      proposta_root_id: null,
      numero_versao: null,
      versao_anterior_id: null,
      is_versao_atual: null,
      is_fechada: null,
      requer_aprovacao: false,
      aprovado_por_id: null,
      aprovado_em: null,
      motivo_revisao: null,
      cpu_desatualizada: false,
    },
  ],
  total: 3,
  page: 1,
  page_size: 20,
};

describe('ProposalsListPage', () => {
  it('renderiza tabela com mock de 3 propostas', async () => {
    server.use(
      http.get('/api/v1/propostas/', ({ request }) => {
        const url = new URL(request.url);
        const clienteId = url.searchParams.get('cliente_id');
        if (clienteId === 'client-1') {
          return HttpResponse.json(mockPropostas);
        }
        return HttpResponse.json({ items: [], total: 0, page: 1, page_size: 20 });
      }),
    );

    renderWithProviders(
      <>
        <ProposalsListPage />
        <LocationCapture />
      </>,
    );

    expect(await screen.findByText('Obra Alpha')).toBeInTheDocument();
    expect(screen.getByText('Obra Beta')).toBeInTheDocument();
    expect(screen.getByText('Obra Gamma')).toBeInTheDocument();
  });

  it('click em linha navega para detail', async () => {
    server.use(
      http.get('/api/v1/propostas/', () => {
        return HttpResponse.json(mockPropostas);
      }),
    );

    renderWithProviders(
      <>
        <ProposalsListPage />
        <LocationCapture />
      </>,
      { initialEntries: ['/propostas'] },
    );

    await screen.findByText('Obra Alpha');

    const row = screen.getByText('Obra Alpha').closest('tr');
    expect(row).toBeTruthy();
    fireEvent.click(row!);

    await waitFor(() => {
      expect(screen.getByTestId('location').textContent).toBe('/propostas/p1');
    });
  });
});
