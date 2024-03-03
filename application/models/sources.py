from pydantic import BaseModel
from typing import Optional

class SourcesItemResponse(BaseModel):
    score: float
    type: str
    name: Optional[str]
    url: Optional[str]