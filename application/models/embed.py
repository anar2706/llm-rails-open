from pydantic import BaseModel
from typing import Optional, Any

class EmbedRequest(BaseModel):
    input: str | list[str]
    model: Optional[str]


class EmbeddingItem(BaseModel):
    object: str
    index: int
    embedding: list[Any]

class EmbedResponse(BaseModel):
    object: str
    data: list[EmbeddingItem]
    model: Optional[str]