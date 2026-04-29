import { describe, it, expect } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { server } from '../../../../test/msw/server';
import { renderWithProviders } from '../../../../test/test-utils';
import { ExpandableTreeRow } from '../ExpandableTreeRow';

const mockComponentes = [
  {
    id: 'comp-1',
    insumo_filho_id: 'ins-1',
    descricao_filho: 'Cimento CP-II',
    codigo_origem: 'CIM-001',
    unidade_medida: 'kg',
    quantidade_consumo: '50.00',
    custo_unitario: '25.00',
    custo_total: '1250.00',
    tipo_recurso: 'INSUMO',
  },
  {
    id: 'comp-2',
    insumo_filho_id: 'srv-2',
    descricao_filho: 'Sub-servico',
    codigo_origem: 'SER.001',
    unidade_medida: 'm2',
    quantidade_consumo: '10.00',
    custo_unitario: '100.00',
    custo_total: '1000.00',
    tipo_recurso: 'SERVICO',
  },
  {
    id: 'comp-3',
    insumo_filho_id: 'ins-3',
    descricao_filho: 'Areia',
    codigo_origem: null,
    unidade_medida: 'm3',
    quantidade_consumo: '2.00',
    custo_unitario: '80.00',
    custo_total: '160.00',
    tipo_recurso: 'INSUMO',
  },
];

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <table>
      <tbody>{children}</tbody>
    </table>
  );
}

describe('ExpandableTreeRow', () => {
  it('linha raiz renderiza com codigo_origem visivel', () => {
    renderWithProviders(
      <Wrapper>
        <ExpandableTreeRow
          item={{
            id: 'srv-1',
            descricao: 'Concreto Usinado',
            codigo_origem: 'CON-001',
            unidade_medida: 'm3',
            custo_unitario: 350,
            tipo_recurso: 'SERVICO',
          }}
        />
      </Wrapper>,
    );

    expect(screen.getByText('Concreto Usinado')).toBeInTheDocument();
    expect(screen.getByText('CON-001')).toBeInTheDocument();
  });

  it('click no chevron dispara fetch de filhos e filhos renderizam com codigo_origem', async () => {
    server.use(
      http.get('/api/v1/servicos/srv-1/componentes', () => {
        return HttpResponse.json(mockComponentes);
      }),
    );

    renderWithProviders(
      <Wrapper>
        <ExpandableTreeRow
          item={{
            id: 'srv-1',
            descricao: 'Concreto Usinado',
            codigo_origem: 'CON-001',
            unidade_medida: 'm3',
            custo_unitario: 350,
            tipo_recurso: 'SERVICO',
          }}
        />
      </Wrapper>,
    );

    const chevron = screen.getByRole('button');
    fireEvent.click(chevron);

    await waitFor(() => {
      expect(screen.getByText('Cimento CP-II')).toBeInTheDocument();
    });

    expect(screen.getByText('CIM-001')).toBeInTheDocument();
    expect(screen.getByText('SER.001')).toBeInTheDocument();
    expect(screen.getByText('—')).toBeInTheDocument(); // Areia sem codigo_origem
  });

  it('recursao de 2 niveis funciona', async () => {
    const mockNivel2 = [
      {
        id: 'comp-n2',
        insumo_filho_id: 'ins-n2',
        descricao_filho: 'Tubo PVC',
        codigo_origem: 'TUB-001',
        unidade_medida: 'un',
        quantidade_consumo: '5.00',
        custo_unitario: '10.00',
        custo_total: '50.00',
        tipo_recurso: 'INSUMO',
      },
    ];

    server.use(
      http.get('/api/v1/servicos/srv-1/componentes', () => {
        return HttpResponse.json(mockComponentes.slice(1, 2));
      }),
      http.get('/api/v1/servicos/srv-2/componentes', () => {
        return HttpResponse.json(mockNivel2);
      }),
    );

    renderWithProviders(
      <Wrapper>
        <ExpandableTreeRow
          item={{
            id: 'srv-1',
            descricao: 'Concreto Usinado',
            codigo_origem: 'CON-001',
            unidade_medida: 'm3',
            custo_unitario: 350,
            tipo_recurso: 'SERVICO',
          }}
        />
      </Wrapper>,
    );

    fireEvent.click(screen.getByRole('button'));
    await waitFor(() => expect(screen.getByText('Sub-servico')).toBeInTheDocument());

    // Expandir nível 2
    fireEvent.click(screen.getByTestId('expand-toggle-srv-2'));

    await waitFor(() => expect(screen.getByText('Tubo PVC')).toBeInTheDocument());
    expect(screen.getByText('TUB-001')).toBeInTheDocument();
  });
});
