from pydantic import BaseModel
from typing import Optional

class UploadResponse(BaseModel):
    status: str = 'ok'
    
    
class TextRequestBody(BaseModel):
    text: str
    name: str
    metadata: Optional[dict]