from pydantic import BaseModel
from typing import Any, Optional

class AppItemResponse(BaseModel):
    id: str
    name: str
    type: str
    created: Optional[int] = 0
    updated: Optional[int] = 0