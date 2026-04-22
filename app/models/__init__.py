# Re-export all models so Alembic autogenerate can detect them
from app.models.associacao_inteligente import AssociacaoInteligente
from app.models.auditoria_log import AuditoriaLog
from app.models.base import Base, TimestampMixin
from app.models.base_tcpo import BaseTcpo
from app.models.categoria_recurso import CategoriaRecurso
from app.models.cliente import Cliente
from app.models.composicao_base import ComposicaoBase
from app.models.composicao_cliente import ComposicaoCliente
from app.models.enums import (
    OrigemAssociacao,
    PerfilUsuario,
    StatusHomologacao,
    StatusValidacaoAssociacao,
    TipoCusto,
    TipoOperacaoAuditoria,
    TipoRecurso,
)
from app.models.historico_busca_cliente import HistoricoBuscaCliente
from app.models.itens_proprios import ItemProprio
from app.models.tcpo_embeddings import TcpoEmbedding
from app.models.usuario import Usuario, UsuarioPerfil
from app.models.versao_composicao import VersaoComposicao
from app.models.pc_tabelas import (
    EtlCarga,
    PcCabecalho,
    PcMaoObraItem,
    PcEquipamentoPremissa,
    PcEquipamentoItem,
    PcEncargoItem,
    PcEpiItem,
    PcEpiDistribuicaoFuncao,
    PcFerramentaItem,
    PcMobilizacaoItem,
    PcMobilizacaoQuantidadeFuncao,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "Usuario",
    "UsuarioPerfil",
    "Cliente",
    "CategoriaRecurso",
    "BaseTcpo",
    "ItemProprio",
    "ComposicaoBase",
    "ComposicaoCliente",
    "VersaoComposicao",
    "TcpoEmbedding",
    "HistoricoBuscaCliente",
    "AssociacaoInteligente",
    "AuditoriaLog",
    # enums
    "TipoCusto",
    "StatusHomologacao",
    "OrigemAssociacao",
    "StatusValidacaoAssociacao",
    "PerfilUsuario",
    "TipoOperacaoAuditoria",
    "TipoRecurso",
]
