"""Schemas for client management endpoints."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClientePcFields(BaseModel):
    razao_social: str | None = Field(default=None, min_length=2, max_length=255)
    inscricao_estadual: str | None = Field(default=None, max_length=30)
    inscricao_municipal: str | None = Field(default=None, max_length=30)
    endereco_logradouro: str | None = Field(default=None, max_length=255)
    endereco_numero: str | None = Field(default=None, max_length=30)
    endereco_complemento: str | None = Field(default=None, max_length=120)
    endereco_bairro: str | None = Field(default=None, max_length=120)
    endereco_municipio: str | None = Field(default=None, max_length=120)
    endereco_uf: str | None = Field(default=None, min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")
    endereco_cep: str | None = Field(default=None, min_length=8, max_length=8, pattern=r"^\d{8}$")
    contato_nome: str | None = Field(default=None, max_length=120)
    contato_email: str | None = Field(default=None, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    contato_telefone: str | None = Field(default=None, max_length=30)

    @field_validator("*", mode="before")
    @classmethod
    def blank_to_none(cls, value: object) -> object:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("endereco_uf", mode="before")
    @classmethod
    def normalize_uf(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().upper()
        return value


class ClienteResponse(ClientePcFields):
    id: UUID
    nome_fantasia: str
    cnpj: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ClienteCreate(ClientePcFields):
    nome_fantasia: str = Field(min_length=2, max_length=255)
    cnpj: str = Field(
        min_length=14,
        max_length=14,
        pattern=r"^\d{14}$",
        description="CNPJ com 14 dígitos numéricos, sem máscara.",
    )


class ClientePatch(ClientePcFields):
    nome_fantasia: str | None = Field(default=None, min_length=2, max_length=255)
    is_active: bool | None = None
