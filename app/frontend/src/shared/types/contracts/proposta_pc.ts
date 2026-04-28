export interface PropostaPcMaoObraOut {
  id: string;
  proposta_id: string;
  bcu_item_id: string | null;
  descricao_funcao: string;
  codigo_origem: string | null;
  quantidade: number | null;
  salario: number | null;
  previsao_reajuste: number | null;
  encargos_percent: number | null;
  periculosidade_insalubridade: number | null;
  refeicao: number | null;
  agua_potavel: number | null;
  vale_alimentacao: number | null;
  plano_saude: number | null;
  ferramentas_val: number | null;
  seguro_vida: number | null;
  abono_ferias: number | null;
  uniforme_val: number | null;
  epi_val: number | null;
  custo_unitario_h: number | null;
  custo_mensal: number | null;
  mobilizacao: number | null;
  valor_bcu_snapshot: number | null;
  editado_manualmente: boolean;
}

export interface PropostaPcEquipamentoPremissaOut {
  id: string;
  proposta_id: string;
  bcu_item_id: string | null;
  horas_mes: number | null;
  preco_gasolina_l: number | null;
  preco_diesel_l: number | null;
  editado_manualmente: boolean;
}

export interface PropostaPcEquipamentoOut {
  id: string;
  proposta_id: string;
  bcu_item_id: string | null;
  codigo: string | null;
  codigo_origem: string | null;
  equipamento: string;
  combustivel_utilizado: string | null;
  consumo_l_h: number | null;
  aluguel_r_h: number | null;
  combustivel_r_h: number | null;
  mao_obra_r_h: number | null;
  hora_produtiva: number | null;
  hora_improdutiva: number | null;
  mes: number | null;
  aluguel_mensal: number | null;
  valor_bcu_snapshot: number | null;
  editado_manualmente: boolean;
}

export interface PropostaPcEncargoOut {
  id: string;
  proposta_id: string;
  bcu_item_id: string | null;
  tipo_encargo: string;
  grupo: string | null;
  codigo_grupo: string | null;
  discriminacao_encargo: string;
  taxa_percent: number | null;
  valor_bcu_snapshot: number | null;
  editado_manualmente: boolean;
}

export interface PropostaPcEpiOut {
  id: string;
  proposta_id: string;
  bcu_item_id: string | null;
  codigo_origem: string | null;
  epi: string;
  unidade: string | null;
  custo_unitario: number | null;
  quantidade: number | null;
  vida_util_meses: number | null;
  custo_epi_mes: number | null;
  valor_bcu_snapshot: number | null;
  editado_manualmente: boolean;
}

export interface PropostaPcFerramentaOut {
  id: string;
  proposta_id: string;
  bcu_item_id: string | null;
  codigo_origem: string | null;
  item: string | null;
  descricao: string;
  unidade: string | null;
  quantidade: number | null;
  preco: number | null;
  preco_total: number | null;
  valor_bcu_snapshot: number | null;
  editado_manualmente: boolean;
}

export interface PropostaPcMobilizacaoOut {
  id: string;
  proposta_id: string;
  bcu_item_id: string | null;
  descricao: string;
  funcao: string | null;
  tipo_mao_obra: string | null;
  editado_manualmente: boolean;
}

export interface DivergenciaOut {
  tabela: 'mao-obra' | 'equipamento' | 'epi' | 'ferramenta' | 'encargo';
  item_id: string;
  campo: string;
  valor_snapshot: number | null;
  valor_atual_bcu: number | null;
  valor_proposta: number | null;
}

export interface RecursoExtraOut {
  id: string;
  proposta_id: string;
  tipo_recurso: string;
  descricao: string;
  unidade_medida: string | null;
  custo_unitario: number;
  observacao: string | null;
  alocacoes_count: number;
}

export interface HistogramaCompletoResponse {
  proposta_id: string;
  bcu_cabecalho_id: string | null;
  mao_obra: PropostaPcMaoObraOut[];
  equipamento_premissa: PropostaPcEquipamentoPremissaOut | null;
  equipamentos: PropostaPcEquipamentoOut[];
  encargos_horista: PropostaPcEncargoOut[];
  encargos_mensalista: PropostaPcEncargoOut[];
  epis: PropostaPcEpiOut[];
  ferramentas: PropostaPcFerramentaOut[];
  mobilizacao: PropostaPcMobilizacaoOut[];
  recursos_extras: RecursoExtraOut[];
  divergencias: DivergenciaOut[];
  cpu_desatualizada: boolean;
}

export interface MontarHistogramaResponse {
  mao_obra: number;
  equipamento_premissa: number;
  equipamentos: number;
  encargos: number;
  epis: number;
  ferramentas: number;
  mobilizacao: number;
}

export interface RecursoExtraCreate {
  tipo_recurso: string;
  descricao: string;
  unidade_medida?: string | null;
  custo_unitario: number;
  observacao?: string | null;
}

export interface RecursoExtraUpdate {
  descricao?: string | null;
  unidade_medida?: string | null;
  custo_unitario?: number | null;
  observacao?: string | null;
}

export interface AlocarRecursoRequest {
  recurso_extra_id: string;
  quantidade_consumo: number;
}

export interface AlocacaoOut {
  id: string;
  recurso_extra_id: string;
  composicao_id: string;
  quantidade_consumo: number;
}
