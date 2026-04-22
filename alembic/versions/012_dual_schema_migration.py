"""Dual-schema architectural migration

Revision ID: 012
Revises: 011
Create Date: 2026-03-29

============================================================================
OVERVIEW
============================================================================
Implements the dual-schema architecture described in der.sql v2:

  referencia.*   — TCPO reference data (OLAP/Lookup, client-free, immutable)
  operacional.*  — Client business layer (OLTP, multi-tenant, governed)

TABLES CREATED:
  referencia.base_tcpo          (from servico_tcpo WHERE origem='TCPO')
  referencia.composicao_base    (from composicao_tcpo TCPO-origin rows)
  operacional.itens_proprios    (from servico_tcpo WHERE origem='PROPRIA')
  operacional.versao_composicao (new structure: item_proprio_id replaces
                                  servico_id + origem + cliente_id)
  operacional.composicao_cliente (new table; dual FK with XOR CHECK)

TABLES MOVED (ALTER TABLE … SET SCHEMA):
  usuarios, clientes, permissao_operacional,
  historico_busca_cliente, auditoria_log  → operacional
  categoria_recurso, tcpo_embeddings      → referencia

COLUMN RENAMES / RESTRUCTURES:
  associacao_inteligente.servico_tcpo_id → item_referencia_id
  tcpo_embeddings FK  : servico_tcpo.id  → referencia.base_tcpo.id
  permissao_operacional.perfil: VARCHAR  → perfil_usuario_enum

TABLES DROPPED:
  composicao_tcpo (replaced by composicao_base + composicao_cliente)
  versao_composicao (old public-schema table; replaced by operacional.versao_composicao)
  servico_tcpo (split into referencia.base_tcpo + operacional.itens_proprios)

ENUMS:
  CREATED: perfil_usuario_enum  (USUARIO | APROVADOR | ADMIN)
  REMOVED: origem_item_enum     (discriminator no longer needed — physical separation)
============================================================================
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ══════════════════════════════════════════════════════════════════════════
    # 0. SCHEMAS
    # ══════════════════════════════════════════════════════════════════════════
    op.execute("CREATE SCHEMA IF NOT EXISTS referencia")
    op.execute("CREATE SCHEMA IF NOT EXISTS operacional")

    # ══════════════════════════════════════════════════════════════════════════
    # 1. ENUMS — create missing, skip if already exists
    # ══════════════════════════════════════════════════════════════════════════
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE perfil_usuario_enum AS ENUM ('USUARIO', 'APROVADOR', 'ADMIN');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    # tipo_recurso_enum may have been created in migrations 001-008; ensure present
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE tipo_recurso_enum AS ENUM (
                'MO', 'INSUMO', 'FERRAMENTA', 'EQUIPAMENTO', 'SERVICO'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # 2. MOVE OPERATIONAL TABLES → operacional SCHEMA
    #    ALTER TABLE … SET SCHEMA is safe: all FKs/indexes move with the table
    #    (they are OID-based, not name-based, in PostgreSQL).
    # ══════════════════════════════════════════════════════════════════════════
    op.execute("ALTER TABLE usuarios SET SCHEMA operacional")
    op.execute("ALTER TABLE clientes SET SCHEMA operacional")
    op.execute("ALTER TABLE permissao_operacional SET SCHEMA operacional")
    op.execute("ALTER TABLE historico_busca_cliente SET SCHEMA operacional")
    op.execute("ALTER TABLE auditoria_log SET SCHEMA operacional")

    # Convert permissao_operacional.perfil from VARCHAR(50) to the new enum
    op.execute("""
        ALTER TABLE operacional.permissao_operacional
            ALTER COLUMN perfil TYPE perfil_usuario_enum
            USING perfil::perfil_usuario_enum;
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # 3. MOVE categoria_recurso → referencia SCHEMA
    #    The SERIAL sequence (categoria_recurso_id_seq) stays in public — that
    #    is harmless since it is referenced by OID in the column default.
    # ══════════════════════════════════════════════════════════════════════════
    op.execute("ALTER TABLE categoria_recurso SET SCHEMA referencia")

    # ══════════════════════════════════════════════════════════════════════════
    # 4. CREATE referencia.base_tcpo
    #    The TCPO catalog: no client columns, no governance workflow.
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "base_tcpo",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("codigo_origem", sa.String(50), nullable=False),
        sa.Column("descricao", sa.Text, nullable=False),
        sa.Column("unidade_medida", sa.String(20), nullable=False),
        sa.Column("custo_base", sa.Numeric(15, 4), nullable=False),
        sa.Column(
            "tipo_recurso",
            postgresql.ENUM(
                "MO", "INSUMO", "FERRAMENTA", "EQUIPAMENTO", "SERVICO",
                name="tipo_recurso_enum",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "categoria_id",
            sa.Integer,
            sa.ForeignKey("referencia.categoria_recurso.id"),
            nullable=True,
        ),
        sa.Column("descricao_tokens", sa.Text, nullable=True),
        sa.Column("metadata_tecnico", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("codigo_origem", name="uq_base_tcpo_codigo_origem"),
        schema="referencia",
    )

    # Populate from servico_tcpo (TCPO-origin only — client-free reference data)
    # custo_unitario → custo_base; metadata_tecnico starts as NULL (not in old schema)
    op.execute("""
        INSERT INTO referencia.base_tcpo (
            id, codigo_origem, descricao, unidade_medida, custo_base,
            tipo_recurso, categoria_id, descricao_tokens, created_at, updated_at
        )
        SELECT
            id, codigo_origem, descricao, unidade_medida, custo_unitario,
            tipo_recurso, categoria_id, descricao_tokens, created_at, updated_at
        FROM servico_tcpo
        WHERE origem = 'TCPO';
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # 5. CREATE referencia.composicao_base  (immutable TCPO BOM)
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "composicao_base",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "servico_pai_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referencia.base_tcpo.id"),
            nullable=False,
        ),
        sa.Column(
            "insumo_filho_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referencia.base_tcpo.id"),
            nullable=False,
        ),
        sa.Column("quantidade_consumo", sa.Numeric(10, 4), nullable=False),
        sa.Column("unidade_medida", sa.String(20), nullable=False),
        schema="referencia",
    )

    # Populate from TCPO-origin compositions.
    # DISTINCT ON handles the edge case of multiple TCPO versions of the same
    # service pair — we keep the first (lowest UUID) to avoid PK collisions.
    # Both servico_pai_id and insumo_filho_id must already be in base_tcpo.
    op.execute("""
        INSERT INTO referencia.composicao_base (
            id, servico_pai_id, insumo_filho_id, quantidade_consumo, unidade_medida
        )
        SELECT DISTINCT ON (ct.servico_pai_id, ct.insumo_filho_id)
            ct.id,
            ct.servico_pai_id,
            ct.insumo_filho_id,
            ct.quantidade_consumo,
            ct.unidade_medida
        FROM composicao_tcpo ct
        JOIN versao_composicao v ON v.id = ct.versao_id
        WHERE v.origem = 'TCPO'
          AND ct.servico_pai_id  IN (SELECT id FROM referencia.base_tcpo)
          AND ct.insumo_filho_id IN (SELECT id FROM referencia.base_tcpo)
        ORDER BY ct.servico_pai_id, ct.insumo_filho_id, ct.id;
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # 6. MOVE tcpo_embeddings → referencia SCHEMA  +  re-key FK
    #    Old FK: tcpo_embeddings.id → servico_tcpo.id  (will be dropped)
    #    New FK: tcpo_embeddings.id → referencia.base_tcpo.id  (same UUIDs)
    # ══════════════════════════════════════════════════════════════════════════
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE tcpo_embeddings
                DROP CONSTRAINT tcpo_embeddings_id_fkey;
        EXCEPTION WHEN undefined_object THEN NULL;
        END $$;
    """)
    op.execute("ALTER TABLE tcpo_embeddings SET SCHEMA referencia")
    op.create_foreign_key(
        "tcpo_embeddings_id_fkey",
        "tcpo_embeddings",
        "base_tcpo",
        ["id"],
        ["id"],
        source_schema="referencia",
        referent_schema="referencia",
        ondelete="CASCADE",
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 7. CREATE operacional.itens_proprios  (client-owned items WITH governance)
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "itens_proprios",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "cliente_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("operacional.clientes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("codigo_origem", sa.String(50), nullable=False),
        sa.Column("descricao", sa.Text, nullable=False),
        sa.Column("unidade_medida", sa.String(20), nullable=False),
        sa.Column("custo_unitario", sa.Numeric(15, 4), nullable=False),
        sa.Column(
            "tipo_recurso",
            postgresql.ENUM(
                "MO", "INSUMO", "FERRAMENTA", "EQUIPAMENTO", "SERVICO",
                name="tipo_recurso_enum",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "categoria_id",
            sa.Integer,
            sa.ForeignKey("referencia.categoria_recurso.id"),
            nullable=True,
        ),
        sa.Column(
            "status_homologacao",
            postgresql.ENUM(
                "PENDENTE", "APROVADO", "REPROVADO",
                name="status_homologacao_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="PENDENTE",
        ),
        sa.Column(
            "aprovado_por_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("operacional.usuarios.id"),
            nullable=True,
        ),
        sa.Column("data_aprovacao", sa.DateTime(timezone=True), nullable=True),
        sa.Column("descricao_tokens", sa.Text, nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        schema="operacional",
    )

    # Populate from servico_tcpo (PROPRIA-origin only; client_id must be set)
    op.execute("""
        INSERT INTO operacional.itens_proprios (
            id, cliente_id, codigo_origem, descricao, unidade_medida,
            custo_unitario, tipo_recurso, categoria_id, status_homologacao,
            aprovado_por_id, data_aprovacao, descricao_tokens, deleted_at,
            created_at, updated_at
        )
        SELECT
            id, cliente_id, codigo_origem, descricao, unidade_medida,
            custo_unitario, tipo_recurso, categoria_id, status_homologacao,
            aprovado_por_id, data_aprovacao, descricao_tokens, deleted_at,
            created_at, updated_at
        FROM servico_tcpo
        WHERE origem = 'PROPRIA'
          AND cliente_id IS NOT NULL;
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # 8. FIX associacao_inteligente
    #    • Drop old FK + index (references servico_tcpo which will be dropped)
    #    • Rename column: servico_tcpo_id → item_referencia_id
    #    • Move table to operacional schema
    #    • Add new FK: item_referencia_id → referencia.base_tcpo.id
    #    (Rename happens BEFORE the SET SCHEMA so table is still in public.)
    # ══════════════════════════════════════════════════════════════════════════
    op.execute("DROP INDEX IF EXISTS public.ix_assoc_inteligente_servico")
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE associacao_inteligente
                DROP CONSTRAINT associacao_inteligente_servico_tcpo_id_fkey;
        EXCEPTION WHEN undefined_object THEN NULL;
        END $$;
    """)
    op.alter_column(
        "associacao_inteligente",
        "servico_tcpo_id",
        new_column_name="item_referencia_id",
    )
    op.execute("ALTER TABLE associacao_inteligente SET SCHEMA operacional")
    op.create_foreign_key(
        "associacao_inteligente_item_referencia_id_fkey",
        "associacao_inteligente",
        "base_tcpo",
        ["item_referencia_id"],
        ["id"],
        source_schema="operacional",
        referent_schema="referencia",
    )
    op.create_index(
        "ix_assoc_inteligente_referencia",
        "associacao_inteligente",
        ["item_referencia_id"],
        schema="operacional",
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 9. CREATE operacional.versao_composicao  (new structure)
    #    Use a temporary name to avoid collision with the old public-schema
    #    versao_composicao that is still alive at this point.
    #    Renamed to versao_composicao in step 12 (after old table is dropped).
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "versao_composicao_v2",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "item_proprio_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("operacional.itens_proprios.id"),
            nullable=False,
        ),
        sa.Column("numero_versao", sa.Integer, nullable=False),
        sa.Column("is_ativa", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "criado_por_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("operacional.usuarios.id"),
            nullable=True,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "item_proprio_id", "numero_versao",
            name="uq_versao_composicao_item_versao",
        ),
        schema="operacional",
    )

    # Migrate only PROPRIA-origin versions whose servico_id now lives in itens_proprios
    op.execute("""
        INSERT INTO operacional.versao_composicao_v2 (
            id, item_proprio_id, numero_versao, is_ativa, criado_por_id, criado_em
        )
        SELECT v.id, v.servico_id, v.numero_versao, v.is_ativa, v.criado_por_id, v.criado_em
        FROM versao_composicao v
        WHERE v.origem = 'PROPRIA'
          AND v.servico_id IN (SELECT id FROM operacional.itens_proprios);
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # 10. CREATE operacional.composicao_cliente  (client BOM — dual FK + XOR)
    # ══════════════════════════════════════════════════════════════════════════
    op.create_table(
        "composicao_cliente",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "versao_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("operacional.versao_composicao_v2.id"),
            nullable=False,
        ),
        sa.Column(
            "insumo_base_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referencia.base_tcpo.id"),
            nullable=True,
        ),
        sa.Column(
            "insumo_proprio_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("operacional.itens_proprios.id"),
            nullable=True,
        ),
        sa.Column("quantidade_consumo", sa.Numeric(10, 4), nullable=False),
        sa.Column("unidade_medida", sa.String(20), nullable=False),
        sa.CheckConstraint(
            "(insumo_base_id IS NOT NULL AND insumo_proprio_id IS NULL) OR "
            "(insumo_base_id IS NULL AND insumo_proprio_id IS NOT NULL)",
            name="ck_composicao_cliente_exclusivo",
        ),
        schema="operacional",
    )

    # Migrate PROPRIA-origin composition items.
    # Determine which FK slot to fill by checking the insumo's origin in servico_tcpo.
    op.execute("""
        INSERT INTO operacional.composicao_cliente (
            id, versao_id,
            insumo_base_id, insumo_proprio_id,
            quantidade_consumo, unidade_medida
        )
        SELECT
            ct.id,
            ct.versao_id,
            CASE WHEN st.origem = 'TCPO'   THEN ct.insumo_filho_id ELSE NULL END,
            CASE WHEN st.origem = 'PROPRIA' THEN ct.insumo_filho_id ELSE NULL END,
            ct.quantidade_consumo,
            ct.unidade_medida
        FROM composicao_tcpo ct
        JOIN versao_composicao  v  ON v.id  = ct.versao_id
        JOIN servico_tcpo       st ON st.id = ct.insumo_filho_id
        WHERE v.origem = 'PROPRIA'
          AND ct.versao_id IN (SELECT id FROM operacional.versao_composicao_v2);
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # 11. DROP OLD TABLES  (in dependency order)
    #
    #   composicao_tcpo  → FK to versao_composicao and servico_tcpo; drop first
    #   versao_composicao → FK to servico_tcpo; drop second
    #   servico_tcpo     → all inbound FKs already removed above; drop last
    # ══════════════════════════════════════════════════════════════════════════
    op.drop_table("composicao_tcpo")
    op.drop_table("versao_composicao")   # old public-schema table
    op.drop_table("servico_tcpo")

    # ══════════════════════════════════════════════════════════════════════════
    # 12. RENAME versao_composicao_v2 → versao_composicao
    #    FK on composicao_cliente.versao_id stays valid (OID-based, not name-based).
    # ══════════════════════════════════════════════════════════════════════════
    op.rename_table("versao_composicao_v2", "versao_composicao", schema="operacional")

    # ══════════════════════════════════════════════════════════════════════════
    # 13. DROP origem_item_enum  (discriminator pattern replaced by physical separation)
    # ══════════════════════════════════════════════════════════════════════════
    op.execute("DROP TYPE IF EXISTS origem_item_enum")

    # ══════════════════════════════════════════════════════════════════════════
    # 14. PRODUCTION INDEXES  (per DER spec — all idempotent via IF NOT EXISTS)
    #
    #   Indexes on moved tables (usuarios, clientes, associacao, etc.) were
    #   preserved by the SET SCHEMA operation — not recreated here.
    # ══════════════════════════════════════════════════════════════════════════

    # ── referencia.base_tcpo ─────────────────────────────────────────────────
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_base_tcpo_descricao_gin "
        "ON referencia.base_tcpo USING gin (descricao gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_base_tcpo_tokens_gin "
        "ON referencia.base_tcpo USING gin (descricao_tokens gin_trgm_ops)"
    )
    op.create_index(
        "ix_base_tcpo_categoria_id", "base_tcpo", ["categoria_id"], schema="referencia"
    )
    op.create_index(
        "ix_base_tcpo_tipo_recurso", "base_tcpo", ["tipo_recurso"], schema="referencia"
    )

    # ── referencia.composicao_base ────────────────────────────────────────────
    op.create_index(
        "ix_composicao_base_pai", "composicao_base", ["servico_pai_id"], schema="referencia"
    )
    op.create_index(
        "ix_composicao_base_filho", "composicao_base", ["insumo_filho_id"], schema="referencia"
    )

    # ── referencia.tcpo_embeddings ────────────────────────────────────────────
    # HNSW index was created conditionally in migration 003 and moved with the
    # table in step 6.  Re-create only if missing (e.g., fresh-install without
    # pgvector at migration 003 time).
    op.execute("""
        DO $emb$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')
            AND NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname = 'referencia'
                  AND tablename  = 'tcpo_embeddings'
                  AND indexname  = 'ix_tcpo_embeddings_hnsw'
            ) THEN
                EXECUTE
                    'CREATE INDEX ix_tcpo_embeddings_hnsw '
                    'ON referencia.tcpo_embeddings '
                    'USING hnsw (vetor vector_cosine_ops) '
                    'WITH (m = 16, ef_construction = 64)';
            END IF;
        END $emb$;
    """)

    # ── operacional.itens_proprios ────────────────────────────────────────────
    op.create_index(
        "ix_itens_proprios_cliente_id",
        "itens_proprios",
        ["cliente_id"],
        schema="operacional",
    )
    op.create_index(
        "ix_itens_proprios_status_hom",
        "itens_proprios",
        ["status_homologacao"],
        schema="operacional",
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_itens_proprios_descricao_gin "
        "ON operacional.itens_proprios USING gin (descricao gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_itens_proprios_tokens_gin "
        "ON operacional.itens_proprios USING gin (descricao_tokens gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_itens_proprios_active "
        "ON operacional.itens_proprios(cliente_id, status_homologacao) "
        "WHERE deleted_at IS NULL"
    )

    # ── operacional.versao_composicao ─────────────────────────────────────────
    op.create_index(
        "ix_versao_composicao_item",
        "versao_composicao",
        ["item_proprio_id"],
        schema="operacional",
    )

    # ── operacional.usuarios / clientes ───────────────────────────────────────
    # ix_usuarios_email, ix_clientes_cnpj, ix_usuarios_external_id_ad
    # already exist and moved with the tables — nothing to create here.

    # ── operacional.associacao_inteligente ────────────────────────────────────
    # ix_assoc_inteligente_cliente, ix_assoc_inteligente_cliente_texto
    # moved with the table in step 8.
    # ix_assoc_inteligente_referencia was created in step 8.


def downgrade() -> None:
    raise NotImplementedError(
        "Migration 012 (dual-schema architectural overhaul) cannot be "
        "automatically reversed.  Restore from a pre-migration database "
        "backup if rollback is required."
    )
