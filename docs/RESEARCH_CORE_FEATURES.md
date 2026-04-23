# Pesquisa de Core — Features Estratégicas para Dinamica Budget

> **Papel:** Research AI  
> **Data:** 2026-04-23  
> **Objetivo:** Promover features voltadas ao core da solução on-premise de orçamentos, com base na análise do DER (`der.sql`) e no fluxo operacional do usuário.

---

## 1. Diagnóstico do Modelo Atual (DER)

### O que está bem modelado

| Componente | Status | Evidência no DER |
|---|---|---|
| **Dual-Schema** (REFERÊNCIA ≠ OPERACIONAL) | ✅ | `referencia.*` imutável, `operacional.*` transacional |
| **Base TCPO** | ✅ | `referencia.base_tcpo` + `composicao_base` (BOM hierárquica) |
| **Busca 4 fases** | ✅ | Fase 0→3 cobertas por índices GIN + HNSW |
| **Associação Inteligente** | ✅ | `associacao_inteligente` com ciclo SUGERIDA→VALIDADA→CONSOLIDADA |
| **Itens Próprios + Homologação** | ✅ | `itens_proprios` com workflow PENDENTE→APROVADO |
| **Composições Customizadas** | ✅ | `versao_composicao` + `composicao_cliente` (XOR FK) |
| **Explosão Recursiva** | ✅ | `composicao_base` expande SERVICO→folhas; código `_explode_recursivo_*` já existe |
| **Propostas + PQ + CPU** | ✅ | Adicionado via migrations (S-09): `propostas`, `pq_itens`, `proposta_itens`, `proposta_item_composicoes` |

### Gaps identificados entre o DER e o fluxo real do usuário

```
FLUXO DO USUÁRIO (esperado)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Admin carrega/atualiza TCPO e PcTabelas (DataCenter)
2. Orçamentista recebe PQ do cliente (Excel)
3. Sistema importa PQ → cria PqItems
4. Busca inteligente cascata encontra match para cada PqItem
5. Usuário confirma/ajusta associações
6. Sistema gera CPU: explode composições × quantidade da PQ
7. Orçamentista visualiza CPU aprovada

GAPS ENCONTRADOS
━━━━━━━━━━━━━━━━━
Gap A: Não há interface web para gestão do DataCenter (carga/edição
       de base_tcpo, composicao_base, categoria_recurso, PcTabelas).
       Hoje é via ETL de Excel ou SQL direto.

Gap B: A importação de PQ é rígida. O usuário disse que "pode ter
       diferentes padrões". O parser atual espera colunas fixas.

Gap C: A Fase 1 (Associação) não tem interface de "treinamento".
       O usuário confirma match, mas não há tela dedicada para
       revisar e consolidar associações em massa.

Gap D: A explosão de composição na CPU precisa garantir que
       composições aninhadas (SERVICO dentro de SERVICO) sejam
       totalmente achatadas (flattened) e que a quantidade da PQ
       seja multiplicada em CADA nível da árvore.

Gap E: PcTabelas (Planilha de Custos) são o coração do cálculo,
       mas não têm CRUD web. O admin precisa subir Excel toda vez.
```

---

## 2. Features Promovidas (prioridade core)

### Feature 1 — DataCenter Manager (Frontend)

**O quê:** Interface web para o administrador gerenciar as tabelas de apoio sem tocar no banco.

**Escopo mínimo:**
- CRUD de `referencia.categoria_recurso`
- CRUD de `referencia.base_tcpo` (com busca por código/descrição)
- Visualização de `referencia.composicao_base` em árvore (tree view)
- Upload de Excel TCPO com preview antes de persistir
- CRUD de PcTabelas (`pc_cabecalho`, `pc_mao_obra_item`, `pc_equipamento_item`, etc.)

**Por que é core:** O usuário disse explicitamente que precisa "gerir o datacenter para atualizar as tabelas de apoio". Hoje isso é feito via ETL ou SQL.

**Dependências:** S-07 (UX Gov) para padrões de tela admin.

---

### Feature 2 — PQ Parser Configurável

**O quê:** Importação de planilha quantitativa com mapeamento dinâmico de colunas.

**Escopo mínimo:**
- Upload do Excel da PQ
- Tela de "mapeamento de colunas": usuário indica qual coluna é Item, Descrição, Quantidade, Unidade, Valor Unitário, Valor Total
- Suporte a múltiplos templates salvos ("Template Petrobras", "Template Odebrecht", etc.)
- Validação: detectar linhas sem descrição ou quantidade
- Preview das primeiras 10 linhas antes de importar

**Por que é core:** O usuário disse "a PQ pode ter diferentes padrões, mas seguem a linha: Item, Descrição, Quantidade, Valor Unitário, Valor Total". O parser atual (`PqImportService`) é rígido.

**Dependências:** S-10 (Importação PQ) — deve ser feito ANTES ou INCLUÍDO no escopo de S-10.

---

### Feature 3 — Console de Associações (Treinamento da IA)

**O quê:** Tela onde o orçamentista revisa, confirma e consolida associações inteligentes em massa.

**Escopo mínimo:**
- Lista paginada de associações por cliente: `texto_busca_normalizado` → `item_referencia.descricao`
- Filtros: status (SUGERIDA / VALIDADA / CONSOLIDADA), origem (MANUAL / IA)
- Ações em massa: "Validar selecionadas", "Consolidar selecionadas", "Remover associação"
- Indicador de confiança (score) com cor (verde >0.8, amarelo 0.5-0.8, vermelho <0.5)
- Estatísticas: "X associações consolidadas = economia de Y segundos por busca"

**Por que é core:** O usuário disse "o usuário vai criando associações e deixando cada vez mais inteligente essa busca". Hoje o loop de feedback existe no backend (`frequencia_uso`, `status_validacao`), mas não há interface dedicada.

**Dependências:** Nenhuma — pode ser feita em paralelo.

---

### Feature 4 — CPU Visualizer (Árvore de Composição)

**O quê:** Tela que exibe a CPU como uma árvore expandida, mostrando cada PqItem → PropostaItem → composição detalhada, com quantidades e custos propagados.

**Escopo mínimo:**
- Árvore recursiva: Proposta → PqItem → PropostaItem → PropostaItemComposicao
- Cada nó folha mostra: descrição, unidade, quantidade base, quantidade da PQ, quantidade total, custo unitário, custo total
- Destaque para itens que vieram de PcTabelas (custo real) vs. itens sem custo encontrado
- Totalizador por tipo de recurso (MO, INSUMO, EQUIPAMENTO, etc.)
- Exportar CPU para Excel/PDF

**Por que é core:** O usuário disse "o resultado esperado da Proposta é ter a CPU com todos os itens da PQ devidamente associados, com suas composições detalhadas". A explosão já existe no backend, mas a visualização é essencial para o orçamentista validar.

**Regra de negócio crítica (Gap D):**
```
quantidade_total_na_CPU = quantidade_consumo_composicao × quantidade_do_item_na_PQ

Se um item da PQ tem Qtd=10, e sua composição tem:
  - Tijolo: qtd_consumo=25
  - Pedreiro: qtd_consumo=0.8h

Na CPU deve aparecer:
  - Tijolo: 25 × 10 = 250 un
  - Pedreiro: 0.8h × 10 = 8h

E se Tijolo for um SERVICO (tem sub-composição), a sub-composição
TAMBÉM deve ser multiplicada por 250 (não por 10).
```

**Dependências:** S-11 (CPU) + S-12 (UX Frontend).

---

### Feature 5 — PcTabelas Quick Editor

**O quê:** Interface web rápida para ajustar custos de mão de obra e equipamento sem subir Excel inteiro.

**Escopo mínimo:**
- Tabela editável in-place (inline editing) para `pc_mao_obra_item` e `pc_equipamento_item`
- Filtro por função/equipamento e por planilha de custos (`pc_cabecalho`)
- Histórico de alterações de custo (audit trail)
- Comparação lado a lado entre duas planilhas de custos

**Por que é core:** As PcTabelas são o "datacenter" de custos. O usuário precisa ajustar salários, encargos, equipamentos com frequência. Subir Excel toda vez é operação pesada.

**Dependências:** S-07 (UX Gov) para padrões de tabela admin.

---

## 3. Recomendação de Priorização

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FASE 1 — Foundation (bloqueia tudo)                                        │
│  ├─ S-09  DONE ✅  Entidades Proposta (base já existe)                      │
│  ├─ S-10 TODO ⏳   Importação PQ + Match                                    │
│  └─ S-11 TODO ⏳   Geração CPU (explosão + PcTabelas lookup)                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  FASE 2 — Core Experience (diferencial competitivo)                         │
│  ├─ Feature 2: PQ Parser Configurável    ← INCLUIR na S-10                  │
│  ├─ Feature 3: Console de Associações    ← NOVA SPRINT (S-13)               │
│  ├─ Feature 4: CPU Visualizer            ← INCLUIR na S-12                  │
│  └─ Feature 5: PcTabelas Quick Editor    ← NOVA SPRINT (S-14)               │
├─────────────────────────────────────────────────────────────────────────────┤
│  FASE 3 — Admin Power (habilita autonomia do cliente)                       │
│  └─ Feature 1: DataCenter Manager        ← NOVA SPRINT (S-15)               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Decisões Técnicas Recomendadas

### 4.1 PropostaItemComposicao — Quantidade Propagada

O DER tem `quantidade_consumo` em `proposta_item_composicoes`, mas NÃO tem `quantidade_total` (propagada). Recomendo:

```sql
-- Adicionar coluna opcional para quantidade já multiplicada
ALTER TABLE operacional.proposta_item_composicoes
ADD COLUMN quantidade_total DECIMAL(15,4) NULL;
```

**Por que:** Evitar recalcular em toda exibição. A quantidade total = `quantidade_consumo × proposta_item.quantidade`. Quando a CPU é gerada, preenche `quantidade_total` junto com `custo_total_insumo`.

### 4.2 Índice Composto para Busca Fase 1

O DER já tem `ix_assoc_inteligente_cliente_texto`, mas com a Feature 3 (Console de Associações), recomendo:

```sql
-- Índice para listagem paginada do console
CREATE INDEX ix_assoc_inteligente_console
ON operacional.associacao_inteligente(cliente_id, status_validacao, origem_associacao);
```

### 4.3 Tabela de Templates de PQ

Para suportar a Feature 2 (PQ Parser Configurável), criar:

```sql
CREATE TABLE operacional.pq_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID NOT NULL REFERENCES operacional.clientes(id),
    nome VARCHAR(100) NOT NULL,           -- "Template Petrobras"
    mapeamento_colunas JSONB NOT NULL,    -- {"item": "A", "descricao": "B", ...}
    delimitador VARCHAR(10) DEFAULT ',',  -- Para CSV
    encoding VARCHAR(20) DEFAULT 'utf-8',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 5. Resumo Executivo

> O core de Dinamica Budget é: **importar PQ → buscar inteligentemente → associar → expl composição → calcular custos → gerar CPU**.
>
> O modelo de dados (DER) já suporta todo esse fluxo. Os gaps estão na **experiência do usuário**: parser flexível, console de associações, visualizador de CPU, e gestão do DataCenter.
>
> As 5 features promovidas focam em transformar o sistema de "funcional" para "produtivo no dia a dia do orçamentista".
