from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class BuscaServicoRequest(BaseModel):
    cliente_id: UUID | None = None  # None → busca genérica (skip fases 0 e 1)
    texto_busca: str = Field(..., min_length=2, max_length=500)
    limite_resultados: int = Field(default=5, ge=1, le=50)
    threshold_score: float = Field(default=0.65, ge=0.0, le=1.0)


class ResultadoBusca(BaseModel):
    id_tcpo: UUID
    codigo_origem: str
    descricao: str
    unidade: str
    custo_unitario: float
    score: float
    score_confianca: float
    origem_match: Literal[
        "ASSOCIACAO_DIRETA", "FUZZY", "IA_SEMANTICA", "PROPRIA_CLIENTE"
    ]
    status_homologacao: str  # StatusHomologacao enum value


class BuscaMetadados(BaseModel):
    """Typed metadata returned alongside search results."""
    tempo_processamento_ms: int
    id_historico_busca: UUID


class BuscaServicoResponse(BaseModel):
    texto_buscado: str
    resultados: list[ResultadoBusca]
    metadados: BuscaMetadados  # typed — replaces previous `dict`


class CriarAssociacaoRequest(BaseModel):
    cliente_id: UUID
    texto_busca_original: str = Field(..., min_length=2, max_length=255)
    id_tcpo_selecionado: UUID
    id_historico_busca: UUID


class AssociacaoResponse(BaseModel):
    status: str
    mensagem: str
    id_associacao: UUID
