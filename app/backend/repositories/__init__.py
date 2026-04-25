from backend.repositories.associacao_repository import AssociacaoRepository
from backend.repositories.base_repository import BaseRepository
from backend.repositories.base_tcpo_repository import BaseTcpoRepository
from backend.repositories.cliente_repository import ClienteRepository
from backend.repositories.historico_repository import HistoricoRepository
from backend.repositories.itens_proprios_repository import ItensPropiosRepository
from backend.repositories.tcpo_embeddings_repository import TcpoEmbeddingsRepository
from backend.repositories.usuario_repository import UsuarioRepository
from backend.repositories.versao_composicao_repository import VersaoComposicaoRepository

__all__ = [
    "AssociacaoRepository",
    "BaseRepository",
    "BaseTcpoRepository",
    "ClienteRepository",
    "HistoricoRepository",
    "ItensPropiosRepository",
    "TcpoEmbeddingsRepository",
    "UsuarioRepository",
    "VersaoComposicaoRepository",
]

