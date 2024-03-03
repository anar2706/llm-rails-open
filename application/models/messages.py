from pydantic import BaseModel, Field
from enum import  IntEnum


class TypeEnum(IntEnum):
    user = 0
    bot = 1


class MessageItem(BaseModel):
    id: str = Field(description='Message id')
    type: TypeEnum = Field(description='Message type. 0 - Bot, 1- User ')
    message: str = Field(description='Message text')
    created: int = Field(description='Created timestamp of message')
    
    
class MessageResponse(BaseModel):
    messages: list[MessageItem]