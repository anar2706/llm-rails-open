from typing import Optional
from pydantic import BaseModel, Extra, Field

class DocsItem(BaseModel):
    name: Optional[str] = ''
    type: str
    url: Optional[str] = ''
    score: float


class ConversationRequestBody(BaseModel, extra=Extra.allow):
    stream: bool
    text: str = Field(description='Text input')
    prompt: Optional[str] = Field(description='Prompt for Conversation AI')
    session_id: Optional[str] = ""
    user_id: Optional[str] = ""
    