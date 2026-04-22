from app.repositories.associacao_repository import AssociacaoRepository
from app.repositories.base_repository import BaseRepository
from app.repositories.base_tcpo_repository import BaseTcpoRepository
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.historico_repository import HistoricoRepository
from app.repositories.itens_proprios_repository import ItensPropiosRepository
from app.repositories.tcpo_embeddings_repository import TcpoEmbeddingsRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.repositories.versao_composicao_repository import VersaoComposicaoRepository

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
