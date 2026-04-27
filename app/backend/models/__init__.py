# Re-export all models so Alembic autogenerate can detect them
from backend.models.associacao_inteligente import AssociacaoInteligente
from backend.models.auditoria_log import AuditoriaLog
from backend.models.base import Base, TimestampMixin
from backend.models.base_tcpo import BaseTcpo
from backend.models.categoria_recurso import CategoriaRecurso
from backend.models.cliente import Cliente
from backend.models.composicao_base import ComposicaoBase
from backend.models.composicao_cliente import ComposicaoCliente
from backend.models.enums import (
    OrigemAssociacao,
    PerfilUsuario,
    StatusImportacao,
    StatusHomologacao,
    PropostaPapel,
    StatusMatch,
    StatusProposta,
    StatusValidacaoAssociacao,
    TipoCusto,
    TipoOperacaoAuditoria,
    TipoRecurso,
    TipoServicoMatch,
)
from backend.models.historico_busca_cliente import HistoricoBuscaCliente
from backend.models.itens_proprios import ItemProprio
from backend.models.tcpo_embeddings import TcpoEmbedding
from backend.models.usuario import Usuario, UsuarioPerfil
from backend.models.versao_composicao import VersaoComposicao
from backend.models.bcu import (
    BcuCabecalho,
    BcuMaoObraItem,
    BcuEquipamentoPremissa,
    BcuEquipamentoItem,
    BcuEncargoItem,
    BcuEpiItem,
    BcuEpiDistribuicaoFuncao,
    BcuFerramentaItem,
    BcuMobilizacaoItem,
    BcuMobilizacaoQuantidadeFuncao,
    DeParaTcpoBcu,
    BcuTableType,
)
from backend.models.proposta import PqImportacao, PqItem, Proposta, PropostaAcl, PropostaItem, PropostaItemComposicao
from backend.models.pq_layout import PqLayoutCliente, PqImportacaoMapeamento  # noqa: F401
from backend.models.proposta_pc import (
    PropostaPcMaoObra,
    PropostaPcEquipamentoPremissa,
    PropostaPcEquipamento,
    PropostaPcEncargo,
    PropostaPcEpi,
    PropostaPcFerramenta,
    PropostaPcMobilizacao,
    PropostaPcMobilizacaoQuantidade,
)
from backend.models.proposta_recurso_extra import (
    PropostaRecursoExtra,
    PropostaRecursoAlocacao,
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
    "Proposta",
    "PqImportacao",
    "PqItem",
    "PropostaItem",
    "PropostaItemComposicao",
    "PropostaAcl",
    "PropostaPapel",
    # enums
    "TipoCusto",
    "StatusHomologacao",
    "OrigemAssociacao",
    "StatusValidacaoAssociacao",
    "PerfilUsuario",
    "TipoOperacaoAuditoria",
    "TipoRecurso",
    "StatusProposta",
    "StatusImportacao",
    "StatusMatch",
    "TipoServicoMatch",
]

