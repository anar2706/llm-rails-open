from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field
from langchain.load.serializable import Serializable

class Document(Serializable):
    text: str
    metadata: dict = Field(default_factory=dict)

class OperatorEnum(str, Enum):
    and_ = 'and'
    or_ = 'or'


class ConditionOperatorEnum(str, Enum):
    eq  = 'eq'
    gt  = 'gt'
    lt  = 'lt'
    gte = 'gte'
    lte = 'lte'


class FilterCondition(BaseModel):
    field: str
    operator: ConditionOperatorEnum
    value: str


class Filter(BaseModel):
    operator: OperatorEnum
    conditions: list[FilterCondition]


class SearchBody(BaseModel):
    k: int = Field(default=5, ge=1, le=10, description='Number of documents to return')
    text: str = Field(description='Query to search for')
    hybrid: Optional[bool] = Field(default=True, description='hybrid search or only vector search')
    summarize: Optional[bool] = Field(default=False, description='Summarize responses or not')
    filters: Optional[Filter] = {}
    
    
class MetadataModel(BaseModel):
    type: str = Field(description='Document source type. One of text, website and file')
    url: str = Field(description='Document url')
    name: str = Field(description='Document name')
    score: float = Field(description='Search score')
    filters: Optional[dict]
 
 
class SearchResponseItem(BaseModel):
    text: str = Field(description='Document text')
    metadata: MetadataModel = Field(description='Document metadata')
    

class SearchResponse(BaseModel):
    results: list[SearchResponseItem]
    summarization: Optional[str] = Field(description='Summarization of responses based on given input')