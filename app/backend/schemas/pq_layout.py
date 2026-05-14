from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, field_validator

from backend.models.enums import CampoSistemaPQ


class MapeamentoItem(BaseModel):
    campo_sistema: CampoSistemaPQ
    coluna_planilha: str


class PqLayoutCriarRequest(BaseModel):
    nome: str = "Layout Padrao"
    aba_nome: str | None = None
    linha_inicio: int = 2
    mapeamentos: list[MapeamentoItem]
    aliases_json: str | None = None

    @field_validator("mapeamentos")
    @classmethod
    def campos_obrigatorios(cls, v: list[MapeamentoItem]) -> list[MapeamentoItem]:
        campos = {m.campo_sistema for m in v}
        ausentes = {CampoSistemaPQ.DESCRICAO, CampoSistemaPQ.QUANTIDADE, CampoSistemaPQ.UNIDADE} - campos
        if ausentes:
            nomes = ", ".join(a.value for a in ausentes)
            raise ValueError(f"Mapeamentos obrigatorios ausentes: {nomes}")
        return v


class MapeamentoItemResponse(BaseModel):
    id: UUID
    campo_sistema: CampoSistemaPQ
    coluna_planilha: str
    model_config = {"from_attributes": True}


class PqLayoutResponse(BaseModel):
    id: UUID
    cliente_id: UUID
    nome: str
    aba_nome: str | None
    linha_inicio: int
    is_aprovado: bool
    aprovado_por_id: UUID | None
    aprovado_em: datetime | None
    aliases_json: str | None
    score_confianca: Decimal | None
    mapeamentos: list[MapeamentoItemResponse]
    model_config = {"from_attributes": True}


class ColunasDetectadasResponse(BaseModel):
    colunas: list[str]
    layout_configurado: bool
    layout_id: UUID | None = None


# ── F4-02 Preview ──────────────────────────────────────────────────────────

class PqPreviewItem(BaseModel):
    linha_planilha: int
    codigo: str | None
    descricao: str
    unidade: str | None
    quantidade: Decimal
    status: str  # "OK" | "ERRO"
    erro_msg: str | None


class PqPreviewResponse(BaseModel):
    score_confianca: Decimal
    linhas_total: int
    linhas_ok: int
    linhas_com_erro: int
    linhas_ignoradas: int = 0
    itens: list[PqPreviewItem]


# ── F4-02 Learning loop / histórico ────────────────────────────────────────

class PqLayoutAprovarRequest(BaseModel):
    pass


class PqLayoutHistoricoResponse(BaseModel):
    id: UUID
    layout_id: UUID
    cliente_id: UUID
    acao: str
    usuario_id: UUID | None
    detalhe_json: str | None
    created_at: datetime
    model_config = {"from_attributes": True}
