from pydantic import BaseModel


class ComputeEmbeddingsResponse(BaseModel):
    status: str
    embeddings_computados: int
