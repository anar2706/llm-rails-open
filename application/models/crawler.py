from pydantic import BaseModel
from enum import Enum

class CrawlTaskRequest(BaseModel):
    link: str
    one_page: bool = False
    
class CrawlTaskResponse(BaseModel):
    id: str
    
    
class CrawlStatusItem(BaseModel):
    id: int
    url: str
    
class Statuses(str, Enum):
    processing = 'processing'
    completed = 'completed'
    
class CrawlStatusResponse(BaseModel):
    status: Statuses
    total: int
    links: list[CrawlStatusItem]
    
    
class VectorizeRequest(BaseModel):
    links: list[CrawlStatusItem]
    

class VectorizeResponse(BaseModel):
    status: str =  'ok'