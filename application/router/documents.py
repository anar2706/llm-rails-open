import time
from fastapi.requests import Request
from fastapi import APIRouter, HTTPException
from application.utils.auth import check_auth
from application.helpers.connections import w_client
from models import Datastores, DatastoresDocuments, db
from application.models.documents import DeleteDocumentBody

router = APIRouter(prefix='/datastores/{datastore_id}/documents')

@router.delete('',tags=['Documents'],name='Delete')
def delete_documents(request: Request, datastore_id: str, arguments: DeleteDocumentBody):
    user_data = check_auth(request.headers)
    record = Datastores.select(Datastores.id, Datastores.vector_id).where(Datastores.pid==datastore_id,
        Datastores.workspace_id==user_data['workspace_id']).dicts()
    
    if not record:
        raise HTTPException(404, 'Schema not found')
    
    record    = record[0]
    documents = arguments.documents

    docs = DatastoresDocuments.select(DatastoresDocuments.id).where(DatastoresDocuments.id.in_(documents), 
            DatastoresDocuments.datastore_id == record['id'])

    for doc in docs:
        print(doc.id)

        result = w_client.batch.delete_objects(
            class_name=record['vector_id'],
            where={
                "operator": "Equal",
                "path": ["doc_id"],
                "valueInt": doc.id
            },
            output="verbose",
            dry_run=False
        )

        a = doc.delete_instance()
        print(f'a {a}')

    return {'status':'ok'}
    