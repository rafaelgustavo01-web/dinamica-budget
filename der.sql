
-- ============================================================================
-- DINÂMICA BUDGET — Diagrama Entidade-Relacionamento (DER)
-- ============================================================================
-- Arquitetura Dual-Schema: REFERÊNCIA (TCPO) ≠ OPERACIONAL (Clientes)
--
-- PRINCÍPIO FUNDAMENTAL:
--   A base TCPO é uma "bíblia" — dados de referência carregados dos arquivos
--   Excel (Composições TCPO - PINI.xlsx, Converter em Data Center.xlsx).
--   Ela NÃO conhece clientes, NÃO tem workflow de aprovação, NÃO tem soft
--   delete. Qualquer carga nova entra e está disponível IMEDIATAMENTE.
--
--   O cliente constrói SUA inteligência em cima dessa base imutável:
--   associações, itens próprios (com homologação), composições customizadas.
--
-- RELACIONAMENTO UNIDIRECIONAL:
--   operacional.* → referencia.*   (cliente descobre a TCPO)
--   referencia.*  ✗ operacional.*  (TCPO nunca aponta para cliente)
--
-- MAPEAMENTO DOS ARQUIVOS EXCEL:
--   "Composições TCPO - PINI.xlsx" → referencia.base_tcpo (serviços/insumos)
--                                   → referencia.composicao_base (hierarquia)
--                                   → referencia.categoria_recurso (categorias)
--   "Converter em Data Center.xlsx" → referencia.base_tcpo (itens adicionais)
--                                   → referencia.categoria_recurso (categorias)
--
-- PIPELINE DE BUSCA (4 fases cascata):
--   Fase 0 — Itens Próprios:    operacional.itens_proprios (filtro: cliente + APROVADO)
--   Fase 1 — Associação Direta: operacional.associacao_inteligente → referencia.base_tcpo
--   Fase 2 — Fuzzy Global:      referencia.base_tcpo (SEM filtros de status — tudo válido)
--   Fase 3 — IA Semântica:      referencia.tcpo_embeddings → referencia.base_tcpo (idem)
--
-- COMPOSIÇÃO EXPLOSION (recursiva):
--   referencia.composicao_base expande SERVICO → folhas (MO, INSUMO, etc.)
--   operacional.composicao_cliente permite o cliente montar composições
--   customizadas usando componentes da base TCPO e/ou itens próprios.
--
-- COMPATIBILIDADE: PostgreSQL 15+ com extensões pgvector, pg_trgm, uuid-ossp
-- TOTAL: 13 tabelas, 7 enums, 3 extensões, 30+ índices
-- ============================================================================


-- ============================================================================
-- 0. EXTENSÕES
-- ============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- gen_random_uuid() já é built-in PG13+, mantido por compat
CREATE EXTENSION IF NOT EXISTS "pg_trgm";     -- Trigramas para busca fuzzy (similaridade textual)
CREATE EXTENSION IF NOT EXISTS "vector";      -- pgvector para busca semântica (embeddings IA)


-- ============================================================================
-- 1. TIPOS ENUM DO POSTGRESQL
-- ============================================================================

-- Categorias de custo para classificação de recursos
CREATE TYPE tipo_custo_enum AS ENUM ('HORISTA', 'MENSALISTA', 'GLOBAL');

-- Classificação funcional de recursos (folhas vs nós na árvore de composição)
CREATE TYPE tipo_recurso_enum AS ENUM ('MO', 'INSUMO', 'FERRAMENTA', 'EQUIPAMENTO', 'SERVICO');

-- Workflow de homologação — SOMENTE para itens_proprios (nunca para base TCPO)
CREATE TYPE status_homologacao_enum AS ENUM ('PENDENTE', 'APROVADO', 'REPROVADO');

-- Origem da associação inteligente
CREATE TYPE origem_associacao_enum AS ENUM ('MANUAL_USUARIO', 'IA_CONSOLIDADA');

-- Ciclo de vida da associação: SUGERIDA → VALIDADA (1+ confirmação) → CONSOLIDADA (3+ confirmações)
CREATE TYPE status_validacao_associacao_enum AS ENUM ('SUGERIDA', 'VALIDADA', 'CONSOLIDADA');

-- Perfis RBAC por cliente (multi-tenant)
CREATE TYPE perfil_usuario_enum AS ENUM ('USUARIO', 'APROVADOR', 'ADMIN');

-- Operações registradas na auditoria
CREATE TYPE tipo_operacao_auditoria_enum AS ENUM ('CREATE', 'UPDATE', 'DELETE', 'APROVAR', 'REPROVAR');


-- ============================================================================
-- 2. CRIAÇÃO DOS SCHEMAS
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS referencia;   -- Base de dados TCPO (OLAP/Lookup — read-heavy, client-free)
CREATE SCHEMA IF NOT EXISTS operacional;  -- Camada de negócio dos clientes (OLTP/Transacional)


-- ############################################################################
--
--   SCHEMA REFERENCIA — A "Bíblia" da TCPO
--
--   Dados carregados dos arquivos Excel. Sem vínculo com cliente.
--   Sem workflow de aprovação. Carga entra e está disponível imediatamente.
--   Nenhuma tabela aqui tem cliente_id, status_homologacao ou deleted_at.
--
-- ############################################################################

-- ============================================================================
-- 3. REFERENCIA: Categoria de Recurso
-- ============================================================================
-- Classifica o tipo de custo dos recursos (Horista, Mensalista, Global).
-- Fonte: abas de classificação dos arquivos Excel TCPO.
CREATE TABLE referencia.categoria_recurso (
    id          SERIAL          PRIMARY KEY,
    descricao   VARCHAR(100)    NOT NULL,
    tipo_custo  tipo_custo_enum NOT NULL
);

COMMENT ON TABLE referencia.categoria_recurso IS
    'Categorias de custo de recursos. Fonte: Excel TCPO. Sem vínculo com cliente.';


-- ============================================================================
-- 4. REFERENCIA: Base TCPO — Catálogo central de serviços e insumos
-- ============================================================================
-- Cada linha é um item do catálogo TCPO (PINI): serviço composto, mão de obra,
-- insumo, ferramenta ou equipamento. Carregado do Excel sem transformação.
-- tipo_recurso=SERVICO indica nó pai (expande via composicao_base).
-- tipo_recurso=MO|INSUMO|FERRAMENTA|EQUIPAMENTO indica folha.
CREATE TABLE referencia.base_tcpo (
    id                UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo_origem     VARCHAR(50)     UNIQUE NOT NULL,      -- Código TCPO (ex: "01.001.001")
    descricao         TEXT            NOT NULL,              -- Descrição completa do item
    unidade_medida    VARCHAR(20)     NOT NULL,              -- m, kg, h, m², vb, etc.
    custo_base        DECIMAL(15,4)   NOT NULL,              -- Custo unitário TCPO (BRL)
    tipo_recurso      tipo_recurso_enum,                     -- MO, INSUMO, FERRAMENTA, EQUIPAMENTO, SERVICO
    categoria_id      INTEGER         REFERENCES referencia.categoria_recurso(id),
    descricao_tokens  TEXT,                                  -- Tokens normalizados (lowercase, sem acentos) para busca trigram
    metadata_tecnico  JSONB,                                 -- Dados analíticos extras do Excel (EPI, combustível, produtividade, etc.)
    created_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE referencia.base_tcpo IS
    'Catálogo TCPO completo. Fonte: Excel (PINI + Data Center). Imutável ao cliente. Sem homologação.';
COMMENT ON COLUMN referencia.base_tcpo.metadata_tecnico IS
    'Dados analíticos extras das planilhas Excel: EPI, combustível, produtividade, coeficientes técnicos.';


-- ============================================================================
-- 5. REFERENCIA: Composição Base — Hierarquia pai-filho TCPO
-- ============================================================================
-- Estrutura de Bill of Materials (BOM) da TCPO. Define quais insumos/recursos
-- compõem cada serviço. Carregado diretamente do Excel.
-- Ex: SERVICO "Alvenaria 1 vez" → MO "Pedreiro" 0.8h + INSUMO "Tijolo" 25un + ...
CREATE TABLE referencia.composicao_base (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    servico_pai_id      UUID            NOT NULL REFERENCES referencia.base_tcpo(id),
    insumo_filho_id     UUID            NOT NULL REFERENCES referencia.base_tcpo(id),
    quantidade_consumo  DECIMAL(10,4)   NOT NULL,            -- Quantidade consumida por unidade do pai
    unidade_medida      VARCHAR(20)     NOT NULL             -- Unidade de consumo do filho
);

COMMENT ON TABLE referencia.composicao_base IS
    'BOM (Bill of Materials) TCPO. Hierarquia pai→filho carregada do Excel. Imutável.';


-- ============================================================================
-- 6. REFERENCIA: Embeddings para Busca Semântica (IA)
-- ============================================================================
-- Vetores de 384 dimensões gerados pelo modelo all-MiniLM-L6-v2 (SentenceTransformers).
-- Relação 1:1 com base_tcpo. Usados na Fase 3 da pipeline de busca (cosine similarity).
-- Não precisa de filtros de status — todo item da base TCPO é válido por definição.
CREATE TABLE referencia.tcpo_embeddings (
    id        UUID        PRIMARY KEY REFERENCES referencia.base_tcpo(id) ON DELETE CASCADE,
    vetor     VECTOR(384),                                   -- Embedding 384D (all-MiniLM-L6-v2)
    metadata  JSONB                                          -- Contexto: descricao, categoria_id, tipo_recurso
);

COMMENT ON TABLE referencia.tcpo_embeddings IS
    'Embeddings IA (pgvector 384D) para busca semântica. 1:1 com base_tcpo. Gerado pelo ML pipeline.';


-- ############################################################################
--
--   SCHEMA OPERACIONAL — Camada de Negócio dos Clientes
--
--   Onde o cliente constrói sua inteligência: usuários, permissões,
--   itens próprios (com homologação), associações com a base TCPO,
--   composições customizadas, histórico de buscas e auditoria.
--
--   Relacionamentos cross-schema são UNIDIRECIONAIS:
--   operacional.* → referencia.base_tcpo (cliente descobre a TCPO)
--   referencia.* NUNCA aponta para operacional.*
--
-- ############################################################################

-- ============================================================================
-- 7. OPERACIONAL: Usuários — Identidade e Autenticação
-- ============================================================================
CREATE TABLE operacional.usuarios (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    nome                VARCHAR(200)    NOT NULL,
    email               VARCHAR(255)    UNIQUE NOT NULL,
    hashed_password     VARCHAR(255)    NOT NULL,            -- Bcrypt/Argon2
    refresh_token_hash  VARCHAR(255),                        -- SHA256 do refresh token (revogação)
    external_id_ad      VARCHAR(255)    UNIQUE,              -- Integração AD/LDAP (objectGUID ou sAMAccountName)
    is_active           BOOLEAN         NOT NULL DEFAULT TRUE,
    is_admin            BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE operacional.usuarios IS
    'Identidade e autenticação. JWT com refresh token revogável. Integração opcional AD/LDAP.';


-- ============================================================================
-- 8. OPERACIONAL: Clientes — Empresas Multi-Tenant
-- ============================================================================
CREATE TABLE operacional.clientes (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    nome_fantasia   VARCHAR(255)    NOT NULL,
    cnpj            VARCHAR(14)     UNIQUE NOT NULL,         -- 14 dígitos (CNPJ brasileiro)
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE operacional.clientes IS
    'Empresas clientes (multi-tenant). CNPJ como identificador de negócio único.';


-- ============================================================================
-- 9. OPERACIONAL: Permissão Operacional — RBAC por Cliente
-- ============================================================================
-- Cada usuário pode ter múltiplos perfis em múltiplos clientes.
-- Ex: João é APROVADOR no Cliente A e USUARIO no Cliente B.
CREATE TABLE operacional.permissao_operacional (
    usuario_id  UUID                    NOT NULL REFERENCES operacional.usuarios(id) ON DELETE CASCADE,
    cliente_id  UUID                    NOT NULL REFERENCES operacional.clientes(id) ON DELETE CASCADE,
    perfil      perfil_usuario_enum     NOT NULL,            -- USUARIO, APROVADOR, ADMIN
    PRIMARY KEY (usuario_id, cliente_id, perfil)
);

COMMENT ON TABLE operacional.permissao_operacional IS
    'RBAC multi-tenant: usuário ↔ cliente ↔ perfil. PK composta garante unicidade.';


-- ============================================================================
-- 10. OPERACIONAL: Itens Próprios — Itens do Cliente COM Homologação
-- ============================================================================
-- Itens criados pelo cliente (ex: insumo regional, mão de obra local).
-- DIFERENTE da base TCPO: estes passam por workflow de aprovação.
-- Somente itens APROVADOS aparecem na busca (Fase 0 da pipeline).
CREATE TABLE operacional.itens_proprios (
    id                      UUID                        PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id              UUID                        NOT NULL REFERENCES operacional.clientes(id) ON DELETE CASCADE,
    codigo_origem           VARCHAR(50)                 NOT NULL,       -- Código interno do cliente
    descricao               TEXT                        NOT NULL,
    unidade_medida          VARCHAR(20)                 NOT NULL,
    custo_unitario          DECIMAL(15,4)               NOT NULL,       -- Custo unitário (BRL)
    tipo_recurso            tipo_recurso_enum,
    categoria_id            INTEGER                     REFERENCES referencia.categoria_recurso(id),
    status_homologacao      status_homologacao_enum     NOT NULL DEFAULT 'PENDENTE',
    aprovado_por_id         UUID                        REFERENCES operacional.usuarios(id),
    data_aprovacao          TIMESTAMPTZ,
    descricao_tokens        TEXT,                                       -- Tokens normalizados para busca trigram
    deleted_at              TIMESTAMPTZ,                                -- Soft delete
    created_at              TIMESTAMPTZ                 NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ                 NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE operacional.itens_proprios IS
    'Itens criados pelo cliente. Passam por homologação (PENDENTE→APROVADO→REPROVADO). Soft delete via deleted_at.';
COMMENT ON COLUMN operacional.itens_proprios.status_homologacao IS
    'Workflow: PENDENTE (criação) → APROVADO (disponível na busca) | REPROVADO (rejeitado pelo aprovador).';


-- ============================================================================
-- 11. OPERACIONAL: Associação Inteligente — Cliente ↔ Base TCPO
-- ============================================================================
-- A inteligência que une o cliente à base TCPO. Quando o usuário busca um
-- termo e seleciona um item da TCPO, essa associação é registrada.
-- Ciclo de vida: SUGERIDA → VALIDADA (1+ uso) → CONSOLIDADA (3+ usos).
-- Associações CONSOLIDADAS retornam imediatamente na Fase 1 da busca.
--
-- FK CROSS-SCHEMA UNIDIRECIONAL:
--   item_referencia_id → referencia.base_tcpo (cliente descobre a TCPO)
--   referencia.base_tcpo NUNCA referencia operacional
CREATE TABLE operacional.associacao_inteligente (
    id                      UUID                                PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id              UUID                                NOT NULL REFERENCES operacional.clientes(id),
    texto_busca_normalizado VARCHAR(255)                        NOT NULL,       -- Texto normalizado (lowercase, sem acentos)
    item_referencia_id      UUID                                NOT NULL REFERENCES referencia.base_tcpo(id),
    origem_associacao       origem_associacao_enum               NOT NULL,       -- MANUAL_USUARIO ou IA_CONSOLIDADA
    confiabilidade_score    DECIMAL(3,2),                                       -- Score de confiança 0.00–1.00
    frequencia_uso          INTEGER                             NOT NULL DEFAULT 1,
    status_validacao        status_validacao_associacao_enum     NOT NULL DEFAULT 'SUGERIDA',
    created_at              TIMESTAMPTZ                         NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ                         NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE operacional.associacao_inteligente IS
    'Associação cliente→TCPO (unidirecional). Fortalece com uso: SUGERIDA→VALIDADA→CONSOLIDADA.';
COMMENT ON COLUMN operacional.associacao_inteligente.frequencia_uso IS
    'Contador de confirmações. ≥3 → CONSOLIDADA (circuit-break na Fase 1 da busca).';


-- ============================================================================
-- 12. OPERACIONAL: Versão de Composição — Versionamento do Cliente
-- ============================================================================
-- O cliente pode manter múltiplas versões de composições para seus itens.
-- Composições TCPO são imutáveis (referencia.composicao_base) — somente
-- o cliente versiona suas composições customizadas.
CREATE TABLE operacional.versao_composicao (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    item_proprio_id     UUID            NOT NULL REFERENCES operacional.itens_proprios(id),
    numero_versao       INTEGER         NOT NULL,
    is_ativa            BOOLEAN         NOT NULL DEFAULT FALSE,
    criado_por_id       UUID            REFERENCES operacional.usuarios(id),
    criado_em           TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    UNIQUE (item_proprio_id, numero_versao)
);

COMMENT ON TABLE operacional.versao_composicao IS
    'Versionamento de composições do cliente. Somente itens_proprios são versionados (TCPO é imutável).';


-- ============================================================================
-- 13. OPERACIONAL: Composição Cliente — BOM Customizado com Dual FK
-- ============================================================================
-- Composições customizadas do cliente. Cada componente pode ser:
--   • Um item da base TCPO (insumo_base_id → referencia.base_tcpo)  OU
--   • Um item próprio do cliente (insumo_proprio_id → itens_proprios)
-- NUNCA ambos — garantido pela CHECK constraint.
CREATE TABLE operacional.composicao_cliente (
    id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    versao_id           UUID            NOT NULL REFERENCES operacional.versao_composicao(id),
    insumo_base_id      UUID            REFERENCES referencia.base_tcpo(id),       -- Se componente é TCPO
    insumo_proprio_id   UUID            REFERENCES operacional.itens_proprios(id),  -- Se componente é item próprio
    quantidade_consumo  DECIMAL(10,4)   NOT NULL,
    unidade_medida      VARCHAR(20)     NOT NULL,
    CONSTRAINT ck_composicao_cliente_exclusivo CHECK (
        (insumo_base_id IS NOT NULL AND insumo_proprio_id IS NULL) OR
        (insumo_base_id IS NULL AND insumo_proprio_id IS NOT NULL)
    )
);

COMMENT ON TABLE operacional.composicao_cliente IS
    'BOM customizado do cliente. Componentes podem ser da TCPO ou itens próprios (exclusivo via CHECK).';
COMMENT ON CONSTRAINT ck_composicao_cliente_exclusivo ON operacional.composicao_cliente IS
    'Garante que cada componente referencia exatamente uma fonte: base TCPO XOR item próprio.';


-- ============================================================================
-- 14. OPERACIONAL: Histórico de Busca — Analytics
-- ============================================================================
-- Registra todas as buscas realizadas. Usado para analytics, aprendizado
-- de padrões e alimentação da associação inteligente.
CREATE TABLE operacional.historico_busca_cliente (
    id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id      UUID            REFERENCES operacional.clientes(id),           -- Nullable: buscas genéricas
    usuario_id      UUID            REFERENCES operacional.usuarios(id) ON DELETE SET NULL,
    texto_busca     TEXT            NOT NULL,
    criado_em       TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE operacional.historico_busca_cliente IS
    'Histórico de buscas para analytics. cliente_id nullable permite buscas genéricas.';


-- ============================================================================
-- 15. OPERACIONAL: Auditoria — Trilha de Operações
-- ============================================================================
-- Registra todas as operações de escrita relevantes no schema operacional.
CREATE TABLE operacional.auditoria_log (
    id                  UUID                            PRIMARY KEY DEFAULT gen_random_uuid(),
    tabela              VARCHAR(100)                    NOT NULL,       -- Nome da tabela afetada
    registro_id         VARCHAR(36)                     NOT NULL,       -- UUID do registro como string
    operacao            tipo_operacao_auditoria_enum    NOT NULL,       -- CREATE, UPDATE, DELETE, APROVAR, REPROVAR
    campo_alterado      VARCHAR(100),                                   -- Coluna modificada (para UPDATE)
    dados_anteriores    JSONB,                                          -- Snapshot antes (UPDATE/DELETE)
    dados_novos         JSONB,                                          -- Snapshot depois (CREATE/UPDATE)
    usuario_id          UUID                            REFERENCES operacional.usuarios(id) ON DELETE SET NULL,
    cliente_id          UUID                            REFERENCES operacional.clientes(id) ON DELETE SET NULL,
    criado_em           TIMESTAMPTZ                     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE operacional.auditoria_log IS
    'Trilha de auditoria completa. Quem fez o quê, quando, com snapshot antes/depois.';


-- ############################################################################
--
--   ÍNDICES DE PERFORMANCE
--
--   Organizados por tabela e tipo:
--   • B-tree: lookups exatos e range queries
--   • GIN + pg_trgm: busca fuzzy por similaridade textual
--   • HNSW + pgvector: busca semântica por similaridade vetorial
--
-- ############################################################################

-- ============================================================================
-- 16. ÍNDICES — Schema REFERENCIA
-- ============================================================================

-- base_tcpo: UNIQUE(codigo_origem) já cria índice B-tree automaticamente

-- base_tcpo: busca fuzzy por descrição (Fase 2 da pipeline)
CREATE INDEX ix_base_tcpo_descricao_gin
    ON referencia.base_tcpo
    USING gin (descricao gin_trgm_ops);

-- base_tcpo: busca fuzzy por tokens normalizados (Fase 2 alternativa)
CREATE INDEX ix_base_tcpo_tokens_gin
    ON referencia.base_tcpo
    USING gin (descricao_tokens gin_trgm_ops);

-- base_tcpo: filtro por categoria
CREATE INDEX ix_base_tcpo_categoria_id
    ON referencia.base_tcpo(categoria_id);

-- base_tcpo: filtro por tipo de recurso
CREATE INDEX ix_base_tcpo_tipo_recurso
    ON referencia.base_tcpo(tipo_recurso);

-- composicao_base: expansão da árvore de composição (recursive CTE)
CREATE INDEX ix_composicao_base_pai
    ON referencia.composicao_base(servico_pai_id);

CREATE INDEX ix_composicao_base_filho
    ON referencia.composicao_base(insumo_filho_id);

-- tcpo_embeddings: busca semântica (Fase 3 — cosine similarity via HNSW)
CREATE INDEX ix_tcpo_embeddings_hnsw
    ON referencia.tcpo_embeddings
    USING hnsw (vetor vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);


-- ============================================================================
-- 17. ÍNDICES — Schema OPERACIONAL
-- ============================================================================

-- usuarios: lookup por email (login)
CREATE INDEX ix_usuarios_email
    ON operacional.usuarios(email);

-- usuarios: lookup por AD (integração) — parcial
CREATE INDEX ix_usuarios_external_id_ad
    ON operacional.usuarios(external_id_ad)
    WHERE external_id_ad IS NOT NULL;

-- clientes: lookup por CNPJ
CREATE INDEX ix_clientes_cnpj
    ON operacional.clientes(cnpj);

-- itens_proprios: filtro por cliente
CREATE INDEX ix_itens_proprios_cliente_id
    ON operacional.itens_proprios(cliente_id);

-- itens_proprios: filtro por status de homologação
CREATE INDEX ix_itens_proprios_status_hom
    ON operacional.itens_proprios(status_homologacao);

-- itens_proprios: busca fuzzy por descrição (Fase 0 da pipeline)
CREATE INDEX ix_itens_proprios_descricao_gin
    ON operacional.itens_proprios
    USING gin (descricao gin_trgm_ops);

-- itens_proprios: busca fuzzy por tokens normalizados (Fase 0 alternativa)
CREATE INDEX ix_itens_proprios_tokens_gin
    ON operacional.itens_proprios
    USING gin (descricao_tokens gin_trgm_ops);

-- itens_proprios: partial index para itens ativos + aprovados (hot path)
CREATE INDEX ix_itens_proprios_active
    ON operacional.itens_proprios(cliente_id, status_homologacao)
    WHERE deleted_at IS NULL;

-- associacao_inteligente: lookup por cliente
CREATE INDEX ix_assoc_inteligente_cliente
    ON operacional.associacao_inteligente(cliente_id);

-- associacao_inteligente: lookup por item de referência
CREATE INDEX ix_assoc_inteligente_referencia
    ON operacional.associacao_inteligente(item_referencia_id);

-- associacao_inteligente: busca direta (Fase 1 — composite key)
CREATE INDEX ix_assoc_inteligente_cliente_texto
    ON operacional.associacao_inteligente(cliente_id, texto_busca_normalizado);

-- versao_composicao: lookup por item próprio
CREATE INDEX ix_versao_composicao_item
    ON operacional.versao_composicao(item_proprio_id);

-- composicao_cliente: lookup por versão
CREATE INDEX ix_composicao_cliente_versao
    ON operacional.composicao_cliente(versao_id);

-- composicao_cliente: partial index por componente TCPO
CREATE INDEX ix_composicao_cliente_base
    ON operacional.composicao_cliente(insumo_base_id)
    WHERE insumo_base_id IS NOT NULL;

-- composicao_cliente: partial index por componente próprio
CREATE INDEX ix_composicao_cliente_proprio
    ON operacional.composicao_cliente(insumo_proprio_id)
    WHERE insumo_proprio_id IS NOT NULL;

-- historico_busca_cliente: filtro por cliente
CREATE INDEX ix_historico_busca_cliente_id
    ON operacional.historico_busca_cliente(cliente_id);

-- historico_busca_cliente: filtro por usuário
CREATE INDEX ix_historico_busca_usuario_id
    ON operacional.historico_busca_cliente(usuario_id);

-- auditoria_log: filtro por tabela
CREATE INDEX ix_auditoria_log_tabela
    ON operacional.auditoria_log(tabela);

-- auditoria_log: filtro por registro
CREATE INDEX ix_auditoria_log_registro
    ON operacional.auditoria_log(registro_id);

-- auditoria_log: filtro por data (range queries em auditoria)
CREATE INDEX ix_auditoria_log_criado_em
    ON operacional.auditoria_log(criado_em);

-- auditoria_log: filtro por usuário
CREATE INDEX ix_auditoria_log_usuario_id
    ON operacional.auditoria_log(usuario_id);

-- auditoria_log: filtro por cliente
CREATE INDEX ix_auditoria_log_cliente_id
    ON operacional.auditoria_log(cliente_id);


-- ############################################################################
--
--   RESUMO DA ARQUITETURA
--
--   Schema REFERENCIA (4 tabelas — read-heavy, client-free):
--     ┌─────────────────────────┐    ┌─────────────────────┐
--     │   categoria_recurso     │    │   tcpo_embeddings    │
--     │   (id, descricao,       │    │   (id FK→base_tcpo,  │
--     │    tipo_custo)          │    │    vetor 384D,       │
--     └──────────┬──────────────┘    │    metadata)         │
--                │ 1:N               └─────────┬───────────┘
--                ▼                              │ 1:1
--     ┌─────────────────────────────────────────▼───────────┐
--     │                  base_tcpo                           │
--     │   (codigo_origem, descricao, custo_base,             │
--     │    tipo_recurso, metadata_tecnico)                   │
--     └──────────┬──────────────┬───────────────────────────┘
--                │ 1:N          │ 1:N
--                ▼              ▼
--     ┌─────────────────────────────┐
--     │     composicao_base         │
--     │   (servico_pai_id,          │
--     │    insumo_filho_id,         │
--     │    quantidade_consumo)      │
--     └─────────────────────────────┘
--
--   Schema OPERACIONAL (9 tabelas — write-heavy, multi-tenant):
--     ┌──────────────┐     ┌──────────────┐
--     │   usuarios   │◄───►│   clientes   │  via permissao_operacional
--     └──────┬───────┘     └──────┬───────┘
--            │                    │
--            ▼                    ▼
--     ┌──────────────────────────────┐
--     │   permissao_operacional      │  PK(usuario_id, cliente_id, perfil)
--     └──────────────────────────────┘
--
--     clientes ──┬──► itens_proprios ──► versao_composicao ──► composicao_cliente
--                │                                                   │
--                │         ┌─ insumo_base_id → referencia.base_tcpo ─┘
--                │         └─ insumo_proprio_id → itens_proprios ────┘
--                │
--                ├──► associacao_inteligente ──► referencia.base_tcpo (cross-schema)
--                │
--                ├──► historico_busca_cliente
--                │
--                └──► auditoria_log
--
-- ############################################################################