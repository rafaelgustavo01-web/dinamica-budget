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
    mapeamentos: list[MapeamentoItemResponse]
    model_config = {"from_attributes": True}


class ColunasDetectadasResponse(BaseModel):
    colunas: list[str]
    layout_configurado: bool
    layout_id: UUID | None = None
