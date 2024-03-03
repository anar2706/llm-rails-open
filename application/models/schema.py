from enum import Enum
from pydantic import BaseModel, Field 
from typing import Optional

class ModelChoices(str, Enum):
    embedding_english_v1 = 'embedding-english-v1'
    embedding_multi_v1 = 'embedding-multi-v1'

class StatusChoices(str, Enum):
    processing = 'processing'
    ready = 'ready'


class AttributeTypeChoices(str, Enum):
    int  = 'int'
    text = 'text'
    number = 'number'


class AttributeItem(BaseModel):
    name: str = Field(description='Field name')
    type: AttributeTypeChoices = Field(description='Field type')


class DataStoreRequest(BaseModel):
    name: str = Field(description='Datastore name')
    description: Optional[str] = Field(description='Datastore description',default=None)
    model: ModelChoices = Field(description='Embedding model')
    metadata: list[AttributeItem] = []
    
    
class DeleteSchmeResponse(BaseModel):
    status: str = 'ok'


class DataStoreStatus(BaseModel):
    status: StatusChoices
    

class CreateDatastoreResponse(BaseModel):
    id: str = Field(description='Created Datastore id')