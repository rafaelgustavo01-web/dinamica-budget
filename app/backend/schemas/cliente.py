"""Schemas for client management endpoints."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ClienteResponse(BaseModel):
    id: UUID
    nome_fantasia: str
    cnpj: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ClienteCreate(BaseModel):
    nome_fantasia: str = Field(min_length=2, max_length=255)
    cnpj: str = Field(
        min_length=14,
        max_length=14,
        pattern=r"^\d{14}$",
        description="CNPJ com 14 dígitos numéricos, sem máscara.",
    )


class ClientePatch(BaseModel):
    nome_fantasia: str | None = Field(default=None, min_length=2, max_length=255)
    is_active: bool | None = None
