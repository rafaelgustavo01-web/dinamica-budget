# Modelagem Conceitual — Módulo de Orçamentos (Fase 2)

> **Autor:** Research AI  
> **Data:** 2026-04-22  
> **Status:** Rascunho para validação do PO  
> **Objetivo:** Definir entidades, fluxo e integração do módulo de orçamentos sem quebrar a Fase 1 (catálogo + homologação + busca).

---

## 1. Visão Geral do Fluxo

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────────────┐
│   PROPOSTA  │────▶│  IMPORTAR PQ    │────▶│  MATCH INTELIGENTE   │
│  (cliente)  │     │ (planilha Excel)│     │ (busca por item)     │
└─────────────┘     └─────────────────┘     └──────────────────────┘
                                                     │
              ┌──────────────────────────────────────┘
              ▼
┌─────────────────────────┐     ┌──────────────────────────────┐
│  SELEÇÃO DO USUÁRIO     │────▶│  EXPLOSÃO DE COMPOSIÇÃO      │
│  (confirma match)       │     │  (ComposicaoBase/Cliente)    │
└─────────────────────────┘     └──────────────────────────────┘
                                             │
              ┌────────────────────────────────┘
              ▼
┌─────────────────────────┐     ┌──────────────────────────────┐
│  CÁLCULO DE CUSTOS      │────▶│  CPU — COMPOSIÇÃO DE PREÇOS  │
│  (PcTabelas satélites)  │     │  UNITÁRIOS (resultado final) │
└─────────────────────────┘     └──────────────────────────────┘
```

**Legenda:**
- **PQ** = Planilha Quantitativa (input bruto do usuário)
- **CPU** = Composição de Preços Unitários (output da proposta)
- **Match** = Busca fuzzy/semântica na cascata BaseTcpo → ItemProprio

---

## 2. Entidades Novas

### 2.1 Proposta (`operacional.propostas`)

Orçamento vinculado a um cliente. Representa uma "proposta comercial" em elaboração.

```python
class Proposta(Base, TimestampMixin):
    __tablename__ = "propostas"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.clientes.id"), nullable=False, index=True)
    criado_por_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.usuarios.id"), nullable=False)

    # Identificação
    codigo: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    titulo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status do workflow
    status: Mapped[StatusProposta] = mapped_column(SAEnum(StatusProposta, ...), nullable=False, default=StatusProposta.RASCUNHO)

    # Controle de versão da CPU
    versao_cpu: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Tabela de custos vigente (qual PC foi usada para calcular)
    pc_cabecalho_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("pc_cabecalho.id"), nullable=True)

    # Totais calculados (denormalizados para performance de leitura)
    total_direto: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    total_indireto: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    total_geral: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    # Timestamps
    data_criacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    data_finalizacao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

**StatusProposta (novo enum):**
- `RASCUNHO` — em elaboração, pode editar
- `EM_ANALISE` — PQ importada, match em andamento
- `CPU_GERADA` — composição calculada, aguardando aprovação
- `APROVADA` — aprovada pelo APROVADOR/ADMIN
- `REPROVADA` — reprovada, volta para RASCUNHO
- `ARQUIVADA` — congelada para histórico

---

### 2.2 PqImportacao (`operacional.pq_importacoes`)

Metadados da importação de uma planilha quantitativa.

```python
class PqImportacao(Base, TimestampMixin):
    __tablename__ = "pq_importacoes"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposta_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.propostas.id"), nullable=False, index=True)

    nome_arquivo: Mapped[str] = mapped_column(String(260), nullable=False)
    formato: Mapped[str] = mapped_column(String(10), nullable=False)  # xlsx, csv
    linhas_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    linhas_importadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    linhas_com_erro: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    status: Mapped[StatusImportacao] = mapped_column(SAEnum(...), nullable=False, default=StatusImportacao.PROCESSANDO)
```

**StatusImportacao (novo enum):**
- `PROCESSANDO` — upload recebido, validando estrutura
- `VALIDADO` — estrutura OK, itens criados
- `COM_ERROS` — algumas linhas falharam (log em campo separado)
- `CONCLUIDO` — todos os itens importados

---

### 2.3 PqItem (`operacional.pq_itens`)

Item bruto importado da planilha quantitativa. Cada linha da PQ vira um PqItem.

```python
class PqItem(Base, TimestampMixin):
    __tablename__ = "pq_itens"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposta_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.propostas.id"), nullable=False, index=True)
    pq_importacao_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.pq_importacoes.id"), nullable=True)

    # Dados brutos da planilha
    codigo_original: Mapped[str | None] = mapped_column(String(50), nullable=True)
    descricao_original: Mapped[str] = mapped_column(Text, nullable=False)
    unidade_medida_original: Mapped[str | None] = mapped_column(String(20), nullable=True)
    quantidade_original: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    # Campos para busca inteligente (normalizados pelo sistema)
    descricao_tokens: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Resultado do match (preenchido após busca)
    match_status: Mapped[StatusMatch] = mapped_column(SAEnum(...), nullable=False, default=StatusMatch.PENDENTE)
    match_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)  # 0.0 a 1.0

    # Match escolhido pelo usuário ou IA
    servico_match_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    servico_match_tipo: Mapped[TipoServicoMatch | None] = mapped_column(SAEnum(...), nullable=True)

    # Metadados de importação
    linha_planilha: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)
```

**StatusMatch (novo enum):**
- `PENDENTE` — aguardando busca
- `BUSCANDO` — motor de busca em execução
- `SUGERIDO` — match encontrado, aguardando confirmação
- `CONFIRMADO` — usuário confirmou o match
- `MANUAL` — usuário selecionou manualmente
- `SEM_MATCH` — nenhum candidato encontrado

**TipoServicoMatch (novo enum):**
- `BASE_TCPO` — match com referencia.base_tcpo
- `ITEM_PROPRIO` — match com operacional.itens_proprios

---

### 2.4 PropostaItem (`operacional.proposta_itens`) — A CPU

Item final da proposta, resultado do match + explosão de composição + cálculo de custos. **Esta é a CPU.**

```python
class PropostaItem(Base, TimestampMixin):
    __tablename__ = "proposta_itens"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposta_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.propostas.id"), nullable=False, index=True)
    pq_item_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.pq_itens.id"), nullable=True)

    # Serviço selecionado (referência ao catálogo)
    servico_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    servico_tipo: Mapped[TipoServicoMatch] = mapped_column(SAEnum(...), nullable=False)

    # Dados do serviço (snapshot no momento da seleção)
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    unidade_medida: Mapped[str] = mapped_column(String(20), nullable=False)

    # Quantidade da PQ
    quantidade: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=Decimal("1"))

    # Custos unitários (vindos da explosão + tabelas satélites)
    custo_material_unitario: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    custo_mao_obra_unitario: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    custo_equipamento_unitario: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    custo_direto_unitario: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    # BDI / Indiretos (percentual aplicado sobre custo direto)
    percentual_indireto: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    custo_indireto_unitario: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    # Preço final unitário
    preco_unitario: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    preco_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    # Origem do cálculo (rastreabilidade)
    composicao_fonte: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "base_tcpo" | "versao_composicao_X"
    pc_cabecalho_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("pc_cabecalho.id"), nullable=True)

    # Ordem de exibição
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
```

---

### 2.5 PropostaItemComposicao (`operacional.proposta_item_composicoes`)

Explosão da composição para um PropostaItem (CPU detalhada). Equivalente a `ComposicaoCliente`, mas vinculada à proposta (transient/draft).

```python
class PropostaItemComposicao(Base):
    __tablename__ = "proposta_item_composicoes"
    __table_args__ = (
        CheckConstraint(
            "(insumo_base_id IS NOT NULL AND insumo_proprio_id IS NULL) OR "
            "(insumo_base_id IS NULL AND insumo_proprio_id IS NOT NULL)",
            name="ck_proposta_item_comp_exclusivo",
        ),
        {"schema": "operacional"},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposta_item_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.proposta_itens.id"), nullable=False, index=True)

    # Insumo (XOR — BaseTcpo OU ItemProprio)
    insumo_base_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("referencia.base_tcpo.id"), nullable=True)
    insumo_proprio_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("operacional.itens_proprios.id"), nullable=True)

    # Dados do insumo no momento da explosão (snapshot)
    descricao_insumo: Mapped[str] = mapped_column(Text, nullable=False)
    unidade_medida: Mapped[str] = mapped_column(String(20), nullable=False)
    quantidade_consumo: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)

    # Custo unitário do insumo (vindo da tabela satélite apropriada)
    custo_unitario_insumo: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    custo_total_insumo: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)

    # Tipo de recurso para agrupamento (MO, INSUMO, EQUIPAMENTO, etc.)
    tipo_recurso: Mapped[TipoRecurso | None] = mapped_column(SAEnum(TipoRecurso, ...), nullable=True)

    # Fonte do custo (rastreabilidade)
    fonte_custo: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "tcpo" | "pc_mao_obra" | "pc_equipamento" | "manual"
```

---

## 3. Tabelas Satélites Já Existentes (Reutilizar)

| Tabela | Schema | Uso na CPU |
|---|---|---|
| `pc_cabecalho` | público | Cabeçalho da Planilha de Custos selecionada |
| `pc_mao_obra_item` | público | Custo de mão de obra por função |
| `pc_equipamento_item` | público | Custo de equipamento (aluguel + combustível) |
| `pc_encargo_item` | público | Taxas de encargo (HORISTA/MENSALISTA) |
| `pc_epi_item` | público | Custo de EPI por função |
| `pc_ferramenta_item` | público | Custo de ferramentas |
| `pc_mobilizacao_item` | público | Custo de mobilização |
| `base_tcpo` | referencia | Preço de referência dos serviços TCPO |
| `itens_proprios` | operacional | Preço dos itens próprios do cliente |
| `composicao_base` | referencia | BOM TCPO para explosão |
| `composicao_cliente` | operacional | BOM customizada para explosão |
| `versao_composicao` | operacional | Controle de versão das composições |

---

## 4. Fluxo Detalhado — Da PQ à CPU

### 4.1 Criar Proposta
```
POST /propostas
→ cria Proposta (RASCUNHO)
→ gera código sequencial (PROP-2026-0001)
```

### 4.2 Importar PQ
```
POST /propostas/{id}/importar-pq
→ recebe arquivo Excel/CSV
→ valida colunas obrigatórias: descricao, unidade_medida, quantidade
→ cria PqImportacao + PqItems
→ retorna status de importação
```

**Colunas esperadas na planilha PQ:**
| Coluna | Obrigatório | Descrição |
|---|---|---|
| `codigo` | Não | Código interno do cliente |
| `descricao` | **Sim** | Descrição do serviço/insumo |
| `unidade_medida` | **Sim** | UN, m², m³, etc. |
| `quantidade` | **Sim** | Quantidade prevista |
| `observacao` | Não | Notas do orçamentista |

### 4.3 Match Inteligente (Busca Cascata)

Para cada `PqItem` com `match_status = PENDENTE`:

```
1. Normalizar descricao_original → descricao_tokens
2. BUSCA 1: Busca semântica/fuzzy em base_tcpo (referencia)
   → Se confiança ≥ 0.85: sugere BASE_TCPO
3. BUSCA 2: Busca semântica/fuzzy em itens_proprios (operacional, APROVADO, do cliente)
   → Se confiança ≥ 0.85: sugere ITEM_PROPRIO
4. BUSCA 3: Busca por código exato (se codigo_original preenchido)
   → Match direto se encontrar
5. Se múltiplos candidatos: retorna top-3 para seleção manual
6. Se nenhum: marca SEM_MATCH
```

**Endpoint:**
```
POST /propostas/{id}/match-automatico
→ processa todos os PqItems pendentes
→ retorna resumo: sugeridos, sem_match, já_confirmados
```

### 4.4 Seleção do Usuário

```
PATCH /propostas/{id}/pq-itens/{pq_item_id}/selecionar-match
→ body: { servico_id, servico_tipo }
→ atualiza PqItem: match_status = CONFIRMADO/MANUAL
```

### 4.5 Gerar CPU (Explosão + Cálculo)

```
POST /propostas/{id}/gerar-cpu
→ para cada PqItem confirmado:
   1. Cria PropostaItem
   2. Explode composição (mesma lógica de explode_composicao do ServicoCatalogService)
   3. Para cada insumo da explosão, resolve custo:
      - Se TipoRecurso.MO → busca em pc_mao_obra_item + pc_encargo_item
      - Se TipoRecurso.EQUIPAMENTO → busca em pc_equipamento_item
      - Se TipoRecurso.INSUMO → usa custo_base (BaseTcpo) ou custo_unitario (ItemProprio)
      - Se TipoRecurso.FERRAMENTA → busca em pc_ferramenta_item
   4. Soma custos → custo_direto_unitario
   5. Aplica percentual_indireto (BDI) → custo_indireto_unitario
   6. Calcula preco_unitario = custo_direto + custo_indireto
   7. Calcula preco_total = preco_unitario * quantidade
→ atualiza Proposta: status = CPU_GERADA
→ atualiza totais na Proposta
```

### 4.6 Exportar / Visualizar CPU

```
GET /propostas/{id}/cpu
→ retorna lista de PropostaItens com composição detalhada
→ formato: JSON para frontend ou Excel para download
```

---

## 5. Integração com Fase 1 (Sem Quebrar)

### 5.1 Princípios de Isolamento

| Regra | Implementação |
|---|---|
| **Não alterar tabelas da Fase 1** | Todas as entidades novas são tabelas novas no schema `operacional` |
| **Não alterar serviços da Fase 1** | Novos services (`PropostaService`, `CpuService`) coexistem com `ServicoCatalogService` |
| **Reutilizar busca existente** | Usar `ServicoCatalogService.list_servicos()` e embeddings para match |
| **Reutilizar explosão existente** | Usar lógica de `explode_composicao()` adaptada para PropostaItem |
| **Reutilizar PcTabelas** | Ler diretamente das tabelas de custo existentes |

### 5.2 Novos Services (arquitetura em camadas)

```
app/services/
├── proposta_service.py         # CRUD de Proposta + workflow
├── pq_import_service.py        # Importação de planilha + validação
├── match_service.py            # Busca inteligente por PqItem
├── cpu_service.py              # Geração da CPU (explosão + cálculo)
└── proposta_composicao_service.py  # Explosão de composição para proposta
```

### 5.3 Novos Endpoints

```
app/api/v1/endpoints/
├── propostas.py           # CRUD + workflow
├── pq_itens.py            # Importação + match
└── cpu.py                 # Geração e consulta da CPU
```

---

## 6. Requisitos Não-Funcionais

1. **Performance:** Match de 500 itens da PQ deve completar em < 30s (batch async)
2. **Consistência:** Se PcTabelas for atualizada, CPU já gerada NÃO muda (snapshot)
3. **Rastreabilidade:** Cada PropostaItem guarda ID do PqItem, do serviço e do PcCabecalho usado
4. **Multi-usuário:** Um orçamentista pode ter múltiplas propostas em RASCUNHO
5. **Segurança:** Proposta só é visível para usuários do mesmo cliente (on-premise rule)

---

## 7. Dependências para Execução

| Pré-requisito | Status | Vínculo |
|---|---|---|
| Arquitetura em camadas (S-02) | `PLAN` | Novos services devem seguir padrão endpoint→service→repository |
| Busca inteligente otimizada (S-05) | `TODO` | Match automático depende de performance da busca |
| PcTabelas populadas | ✅ OK | Dados já carregados via ETL |
| BaseTcpo + ComposicaoBase | ✅ OK | Catálogo TCPO completo |

---

## 8. Próximos Passos Sugeridos

1. **PO valida** este modelo conceitual
2. **Supervisor** gera plano técnico detalhado (sprints S-09, S-10, S-11)
3. **Worker** implementa por fases:
   - Fase 2a: Entidades + CRUD Proposta
   - Fase 2b: Importação PQ + match inteligente
   - Fase 2c: Geração CPU + explosão + cálculo de custos
   - Fase 2d: UI/UX de orçamentos (frontend)

---

*Documento gerado por Research AI em 2026-04-22.*
*Aguardando validação do Product Owner para incorporação no ROADMAP.*
