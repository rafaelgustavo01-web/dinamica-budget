from pydantic import BaseModel


class ComputeEmbeddingsResponse(BaseModel):
    status: str
    embeddings_computados: int


class SystemSettingsResponse(BaseModel):
    proposal_number_pattern: str


class SystemSettingsUpdate(BaseModel):
    proposal_number_pattern: str
