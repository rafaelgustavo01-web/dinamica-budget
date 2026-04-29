import { describe, it, expect } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { server } from '../../../../test/msw/server';
import { renderWithProviders } from '../../../../test/test-utils';
import { HistogramaPage } from '../ProposalHistogramaPage';

const mockHistograma = {
  proposta_id: '123',
  bcu_cabecalho_id: 'bcu-1',
  mao_obra: [
    {
      id: 'mo-1',
      proposta_id: '123',
      bcu_item_id: 'bci-1',
      descricao_funcao: 'Pedreiro',
      codigo_origem: 'MO-001',
      quantidade: 2,
      salario: 3500,
      previsao_reajuste: null,
      encargos_percent: 85,
      periculosidade_insalubridade: null,
      refeicao: null,
      agua_potavel: null,
      vale_alimentacao: null,
      plano_saude: null,
      ferramentas_val: null,
      seguro_vida: null,
      abono_ferias: null,
      uniforme_val: null,
      epi_val: null,
      custo_unitario_h: 45.5,
      custo_mensal: 7000,
      mobilizacao: null,
      valor_bcu_snapshot: 45.5,
      editado_manualmente: false,
    },
  ],
  equipamento_premissa: null,
  equipamentos: [
    {
      id: 'eq-1',
      proposta_id: '123',
      bcu_item_id: 'bci-2',
      codigo: 'EQ-001',
      codigo_origem: 'EQ-001',
      equipamento: 'Betoneira',
      combustivel_utilizado: null,
      consumo_l_h: null,
      aluguel_r_h: 15.5,
      combustivel_r_h: null,
      mao_obra_r_h: null,
      hora_produtiva: null,
      hora_improdutiva: null,
      mes: null,
      aluguel_mensal: null,
      valor_bcu_snapshot: 15.5,
      editado_manualmente: false,
    },
  ],
  encargos_horista: [],
  encargos_mensalista: [],
  epis: [],
  ferramentas: [],
  mobilizacao: [],
  recursos_extras: [],
  divergencias: [
    {
      tabela: 'mao-obra',
      item_id: 'mo-1',
      campo: 'custo_unitario_h',
      valor_snapshot: 3500,
      valor_atual_bcu: 3800,
      valor_proposta: 3500,
    },
  ],
  cpu_desatualizada: true,
};

describe('ProposalHistogramaPage', () => {
  it('renderiza pagina sem crash com mock de histograma', async () => {
    server.use(
      http.get('/api/v1/propostas/123/histograma', () => {
        return HttpResponse.json(mockHistograma);
      }),
    );

    renderWithProviders(<HistogramaPage />, {
      route: '/propostas/123/histograma',
      path: '/propostas/:id/histograma',
    });

    expect(await screen.findByText('Histograma da Proposta')).toBeInTheDocument();
    expect(await screen.findByText('Pedreiro')).toBeInTheDocument();
    expect(await screen.findByText('CPU Desatualizada')).toBeInTheDocument();
  });

  it('troca de aba (MO -> EQP) muda conteudo da tabela', async () => {
    server.use(
      http.get('/api/v1/propostas/123/histograma', () => {
        return HttpResponse.json(mockHistograma);
      }),
    );

    renderWithProviders(<HistogramaPage />, {
      route: '/propostas/123/histograma',
      path: '/propostas/:id/histograma',
    });

    await screen.findByText('Pedreiro');

    const tabEquipamentos = screen.getByRole('tab', { name: /Equipamentos/i });
    fireEvent.click(tabEquipamentos);

    await waitFor(() => {
      expect(screen.getByText('Betoneira')).toBeInTheDocument();
    });
    expect(screen.getByText('Aluguel R$/h')).toBeInTheDocument();
  });

  it('badge de divergencia aparece quando valor_atual != valor_snapshot', async () => {
    server.use(
      http.get('/api/v1/propostas/123/histograma', () => {
        return HttpResponse.json(mockHistograma);
      }),
    );

    renderWithProviders(<HistogramaPage />, {
      route: '/propostas/123/histograma',
      path: '/propostas/:id/histograma',
    });

    await screen.findByText('Pedreiro');

    expect(screen.getByText('1 divergência(s) com BCU')).toBeInTheDocument();
    expect(screen.getByText('Diverge')).toBeInTheDocument();
  });

  it('edicao inline de uma celula dispara mutation com payload correto', async () => {
    let patched = false;
    let capturedBody: Record<string, unknown> | null = null;
    server.use(
      http.get('/api/v1/propostas/123/histograma', () => {
        return HttpResponse.json(mockHistograma);
      }),
      http.patch('/api/v1/propostas/123/histograma/mao-obra/mo-1', async ({ request }) => {
        capturedBody = (await request.json()) as Record<string, unknown>;
        patched = true;
        return HttpResponse.json({ ok: true });
      }),
    );

    renderWithProviders(<HistogramaPage />, {
      route: '/propostas/123/histograma',
      path: '/propostas/:id/histograma',
    });

    await screen.findByText('Pedreiro');

    const salarioInput = screen.getAllByRole('spinbutton')[0];
    fireEvent.change(salarioInput, { target: { value: '4000' } });
    fireEvent.blur(salarioInput);

    await waitFor(() => expect(patched).toBe(true));
    expect(capturedBody).toEqual(expect.objectContaining({ salario: 4000 }));
  });
});
