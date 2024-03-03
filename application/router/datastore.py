import time
from fastapi.requests import Request
from fastapi import APIRouter, HTTPException
from application.utils.auth import check_auth
from application.helpers.connections import w_client
from application.utils.general import generate_md5, generate_uuid
from models import Datastores, DatastoresDocuments
from application.models.schema import (DataStoreRequest, DeleteSchmeResponse, 
        DataStoreStatus, CreateDatastoreResponse)

router = APIRouter(prefix='/datastores')


@router.get('/{datastore_id}',tags=['Datastores'],name='Status')
def get_datastore_status(request: Request, datastore_id: str) -> DataStoreStatus:
    user_data = check_auth(request.headers)
    record = Datastores.select(Datastores.id, Datastores.vector_id).where(Datastores.pid==datastore_id,
        Datastores.workspace_id==user_data['workspace_id']).dicts()
    
    if not record:
        raise HTTPException(404, 'Schema not found')
    
    documents = DatastoresDocuments.select().where(DatastoresDocuments.datastore_id==record[0]['id'],
        DatastoresDocuments.workspace_id==user_data['workspace_id'],DatastoresDocuments.status==0).dicts()
    
    if documents:
        return {'status':'processing'}
    
    return {'status':'ready'}


@router.post('',tags=['Datastores'],name='Create')
def create_datastore(request: Request, arguments: DataStoreRequest) -> CreateDatastoreResponse:
    user_data   = check_auth(request.headers)
    arguments   = arguments.dict()
    schema_pid  = f"dst_{generate_uuid()}"
    vector_id   = f'Class_{generate_md5(schema_pid)}'
    description = arguments.get('description')
    print(vector_id)

    record_exists = Datastores.select().where(Datastores.name==arguments['name']).where(
        Datastores.workspace_id==user_data['workspace_id']).dicts()
    
    if record_exists:
        raise HTTPException(404, 'Datastore exists with this name in workspace')
    
    reserved_keys = ('text', 'type', 'name', 'url', 'doc_id')
    data = {
        "class": vector_id,
        "description": description if description else "",
        "properties": [
            {   
                "name": "text",
                'dataType':["text"]
            },
            {   
                "name": "type",
                'dataType':["text"],
                "indexFilterable": False,
                "indexSearchable": False,
            },
            {   
                "name": "name",
                'dataType':["text"],
                "indexFilterable": False,
                "indexSearchable": False,
            },
            {   
                "name": "url",
                'dataType':["text"],
                "indexFilterable": False,
                "indexSearchable": False,
            },
            {   
                "name": "doc_id",
                'dataType':["int"],
                "indexFilterable": True,
                "indexSearchable": False,
            }
        ]
    }
    
    metadata = arguments.get('metadata',[])
    for field in metadata:
        if field['name'] in reserved_keys:
            raise HTTPException(400, f'Metadata field name `{field["name"]}` is one of reserved keys. Change it')

        data['properties'].append(
            {   
                "name": field['name'],
                'dataType':[field['type']],
                'indexSearchable':False
            }
        )
    
    w_client.schema.create_class(data)
    Datastores.create(name=arguments['name'],description=description,
        embedding_model=arguments['model'],attributes=metadata,user_id=user_data['user_id'],
        pid=schema_pid,workspace_id=user_data['workspace_id'],vector_id=vector_id,
        created=time.time()).id
    
    return {'id':schema_pid}



@router.delete('/{datastore_id}',tags=['Datastores'],name='Delete')
def delete_datastore(request: Request, datastore_id: str) -> DeleteSchmeResponse:
    user_data = check_auth(request.headers)
    record = Datastores.select(Datastores.id, Datastores.vector_id).where(Datastores.pid==datastore_id,
        Datastores.workspace_id==user_data['workspace_id']).dicts()
    
    if not record:
        raise HTTPException(404, 'Schema not found')
    
    active_tasks = DatastoresDocuments.select().where(DatastoresDocuments.datastore_id==record[0]['id'], 
            DatastoresDocuments.status==0).dicts()
    
    if active_tasks:
        raise HTTPException(400, "Datastore could not be deleted. There are active indexing tasks.")

    class_name = record[0]['vector_id']
    w_client.schema.delete_class(class_name)
    
    Datastores.delete().where(Datastores.id==record[0]['id']).execute()
    DatastoresDocuments.delete().where(DatastoresDocuments.datastore_id==record[0]['id']).execute()
    
    return {'status':'ok'}
    