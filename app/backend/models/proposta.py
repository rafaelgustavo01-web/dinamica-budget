import uuid
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin
from backend.models.enums import PropostaPapel, StatusImportacao, StatusMatch, StatusProposta, TipoRecurso, TipoServicoMatch


class Proposta(Base, TimestampMixin):
    __tablename__ = "propostas"
    __table_args__ = (
        UniqueConstraint("proposta_root_id", "numero_versao", name="uq_proposta_versao"),
        {"schema": "operacional"},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.clientes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    criado_por_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.usuarios.id"),
        nullable=False,
    )
    codigo: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    titulo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[StatusProposta] = mapped_column(
        SAEnum(StatusProposta, name="status_proposta_enum", create_type=False),
        nullable=False,
        default=StatusProposta.RASCUNHO,
    )
    versao_cpu: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    pc_cabecalho_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("pc_cabecalho.id"),
        nullable=True,
    )
    total_direto: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    total_indireto: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    total_geral: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    data_finalizacao: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    # Versionamento
    proposta_root_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True, index=True
    )
    numero_versao: Mapped[int | None] = mapped_column(Integer, nullable=True, default=1)
    versao_anterior_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.propostas.id"),
        nullable=True,
    )
    is_versao_atual: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=True)
    is_fechada: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)

    # Aprovação
    requer_aprovacao: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    aprovado_por_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.usuarios.id"),
        nullable=True,
    )
    aprovado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    motivo_revisao: Mapped[str | None] = mapped_column(Text, nullable=True)

    cliente: Mapped["Cliente"] = relationship("Cliente", lazy="noload")
    criado_por: Mapped["Usuario"] = relationship("Usuario", foreign_keys="[Proposta.criado_por_id]", lazy="noload")
    pq_importacoes: Mapped[list["PqImportacao"]] = relationship(
        back_populates="proposta",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    pq_itens: Mapped[list["PqItem"]] = relationship(
        back_populates="proposta",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    itens: Mapped[list["PropostaItem"]] = relationship(
        back_populates="proposta",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    resumo_recursos: Mapped[list["PropostaResumoRecurso"]] = relationship(
        back_populates="proposta",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    acl_entries: Mapped[list["PropostaAcl"]] = relationship(
        back_populates="proposta",
        lazy="noload",
        cascade="all, delete-orphan",
    )


class PqImportacao(Base, TimestampMixin):
    __tablename__ = "pq_importacoes"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposta_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.propostas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nome_arquivo: Mapped[str] = mapped_column(String(260), nullable=False)
    formato: Mapped[str] = mapped_column(String(10), nullable=False)
    linhas_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    linhas_importadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    linhas_com_erro: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[StatusImportacao] = mapped_column(
        SAEnum(StatusImportacao, name="status_importacao_enum", create_type=False),
        nullable=False,
        default=StatusImportacao.PROCESSANDO,
    )

    proposta: Mapped[Proposta] = relationship(back_populates="pq_importacoes", lazy="noload")
    itens: Mapped[list["PqItem"]] = relationship(back_populates="pq_importacao", lazy="noload")


class PqItem(Base, TimestampMixin):
    __tablename__ = "pq_itens"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposta_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.propostas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pq_importacao_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.pq_importacoes.id", ondelete="SET NULL"),
        nullable=True,
    )
    codigo_original: Mapped[str | None] = mapped_column(String(50), nullable=True)
    descricao_original: Mapped[str] = mapped_column(Text, nullable=False)
    unidade_medida_original: Mapped[str | None] = mapped_column(String(20), nullable=True)
    quantidade_original: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    descricao_tokens: Mapped[str | None] = mapped_column(Text, nullable=True)
    match_status: Mapped[StatusMatch] = mapped_column(
        SAEnum(StatusMatch, name="status_match_enum", create_type=False),
        nullable=False,
        default=StatusMatch.PENDENTE,
    )
    match_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    servico_match_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    servico_match_tipo: Mapped[TipoServicoMatch | None] = mapped_column(
        SAEnum(TipoServicoMatch, name="tipo_servico_match_enum", create_type=False),
        nullable=True,
    )
    linha_planilha: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)

    proposta: Mapped[Proposta] = relationship(back_populates="pq_itens", lazy="noload")
    pq_importacao: Mapped[PqImportacao | None] = relationship(back_populates="itens", lazy="noload")
    proposta_itens: Mapped[list["PropostaItem"]] = relationship(back_populates="pq_item", lazy="noload")


class PropostaItem(Base, TimestampMixin):
    __tablename__ = "proposta_itens"
    __table_args__ = {"schema": "operacional"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposta_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.propostas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pq_item_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.pq_itens.id", ondelete="SET NULL"),
        nullable=True,
    )
    servico_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    servico_tipo: Mapped[TipoServicoMatch] = mapped_column(
        SAEnum(TipoServicoMatch, name="tipo_servico_match_enum", create_type=False),
        nullable=False,
    )
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    unidade_medida: Mapped[str] = mapped_column(String(20), nullable=False)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=Decimal("1"))
    custo_material_unitario: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    custo_mao_obra_unitario: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    custo_equipamento_unitario: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    custo_direto_unitario: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    percentual_indireto: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    custo_indireto_unitario: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    preco_unitario: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    preco_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    composicao_fonte: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pc_cabecalho_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("pc_cabecalho.id"), nullable=True)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    proposta: Mapped[Proposta] = relationship(back_populates="itens", lazy="noload")
    pq_item: Mapped[PqItem | None] = relationship(back_populates="proposta_itens", lazy="noload")
    composicoes: Mapped[list["PropostaItemComposicao"]] = relationship(
        back_populates="proposta_item",
        lazy="noload",
        cascade="all, delete-orphan",
    )


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
    proposta_item_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.proposta_itens.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    insumo_base_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("referencia.base_tcpo.id"),
        nullable=True,
    )
    insumo_proprio_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.itens_proprios.id"),
        nullable=True,
    )
    descricao_insumo: Mapped[str] = mapped_column(Text, nullable=False)
    unidade_medida: Mapped[str] = mapped_column(String(20), nullable=False)
    quantidade_consumo: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    custo_unitario_insumo: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    custo_total_insumo: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    tipo_recurso: Mapped[TipoRecurso | None] = mapped_column(
        SAEnum(TipoRecurso, name="tipo_recurso_enum", create_type=False),
        nullable=True,
    )
    fonte_custo: Mapped[str | None] = mapped_column(String(50), nullable=True)

    pai_composicao_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.proposta_item_composicoes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    nivel: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    e_composicao: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    composicao_explodida: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    sub_composicoes: Mapped[list["PropostaItemComposicao"]] = relationship(
        back_populates="pai",
        lazy="noload",
        cascade="all, delete-orphan",
        foreign_keys="[PropostaItemComposicao.pai_composicao_id]",
    )
    pai: Mapped["PropostaItemComposicao | None"] = relationship(
        back_populates="sub_composicoes",
        lazy="noload",
        foreign_keys="[PropostaItemComposicao.pai_composicao_id]",
        remote_side="[PropostaItemComposicao.id]",
    )

    proposta_item: Mapped[PropostaItem] = relationship(back_populates="composicoes", lazy="noload")


class PropostaResumoRecurso(Base):
    __tablename__ = "proposta_resumo_recursos"
    __table_args__ = (
        CheckConstraint("total_direto >= 0", name="ck_resumo_direto_positivo"),
        CheckConstraint("total_indireto >= 0", name="ck_resumo_indireto_positivo"),
        CheckConstraint("total_geral >= 0", name="ck_resumo_geral_positivo"),
        {"schema": "operacional"},
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposta_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.propostas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo_recurso: Mapped[str] = mapped_column(String(50), nullable=False)
    total_direto: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=Decimal("0"))
    total_indireto: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=Decimal("0"))
    total_geral: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=Decimal("0"))
    data_atualizacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    proposta: Mapped[Proposta] = relationship(back_populates="resumo_recursos", lazy="noload")


class PropostaAcl(Base, TimestampMixin):
    __tablename__ = "proposta_acl"
    __table_args__ = (
        UniqueConstraint("proposta_id", "usuario_id", "papel", name="uq_proposta_acl"),
        {"schema": "operacional"},
    )
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposta_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.propostas.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    usuario_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.usuarios.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    papel: Mapped["PropostaPapel"] = mapped_column(
        SAEnum(PropostaPapel, name="proposta_papel_enum", create_type=False), nullable=False,
    )
    created_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("operacional.usuarios.id"),
        nullable=False,
    )

    proposta: Mapped["Proposta"] = relationship(back_populates="acl_entries", lazy="noload")
