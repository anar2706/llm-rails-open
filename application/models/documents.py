from pydantic import BaseModel

class DeleteDocumentBody(BaseModel):
    documents: list[int]