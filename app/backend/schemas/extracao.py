"""
Schemas for /extracao endpoints.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ServicoClienteAssociado(BaseModel):
    """
    A catalog item as seen from a specific client's perspective.
    descricao_cliente → the text the client uses (from associacao_inteligente)
    descricao_tcpo    → the original TCPO description
    """

    model_config = ConfigDict(from_attributes=True)

    id: str                    # associacao_inteligente.id
    item_referencia_id: str    # base_tcpo.id (use for BOM explosion)
    descricao_cliente: str     # texto_busca_normalizado
    frequencia_uso: int
    codigo_origem: str
    descricao_tcpo: str
    unidade_medida: str
    custo_base: float
    tipo_recurso: str | None = None
