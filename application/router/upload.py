import os
import uuid
import time
import json
from fastapi import Request, Form
from project.celery import app as c_app
from werkzeug.utils import secure_filename
from fastapi import APIRouter,File, UploadFile,HTTPException
from application.utils.auth import check_auth
from models import Datastores, DatastoresDocuments
from application.utils.upload import upload_to_aws
from application.models.upload import UploadResponse, TextRequestBody


router = APIRouter(prefix='/datastores/{datastore_id}')

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'upload')


@router.post('/text',description='Upload Text',name='Text',tags=['Upload'])
def upload_text(request: Request, datastore_id: str, arguments: TextRequestBody) -> UploadResponse:
    user_data = check_auth(request.headers)
    
    record = Datastores.select(Datastores.id, Datastores.pid, Datastores.embedding_model, 
            Datastores.attributes, Datastores.vector_id).where(Datastores.pid==datastore_id).dicts()
    
    if not record:
        raise HTTPException(404, 'Datastore not found')
    
    document_id = DatastoresDocuments.create(type='text',name=arguments.name,bytes=0,
        tokens=0,datastore_id=record[0]['id'],user_id=user_data['user_id'],
        workspace_id=user_data['workspace_id'],meta={'text':arguments.text},created=time.time()).id
    

    c_app.send_task(
        "semantic.upload_text_vector",
        kwargs={
            'text': arguments.text, 
            'user':user_data,
            'name':arguments.name,
            'datastore': record[0], 
            'document_id':document_id,
            'metadata': arguments.metadata if arguments.metadata else {}
        },queue="semantic",
    )
    
    return {'status':'ok'}
    

@router.post('/file',description='Upload file',name='File',tags=['Upload'])
async def upload_file(request: Request, datastore_id: str, metadata: str = Form(None) ,file: list[UploadFile] = File(...)) -> UploadResponse:
    files = file
    user_data = check_auth(request.headers)
    max_file_size = 15728640
    valid_formats = ['application/pdf','application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/csv','text/plain','application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','text/x-script.python']

    record = Datastores.select(Datastores.id, Datastores.vector_id, Datastores.embedding_model,
        Datastores.attributes).where(Datastores.pid==datastore_id).dicts()
    
    if not record:
        raise HTTPException(404, 'Datastore not found')
    
    errors = []
    
    for file in files:

        original_filename = secure_filename(file.filename)
        filename = uuid.uuid4().hex
                
        with open(os.path.join(UPLOAD_FOLDER, filename),'wb+') as f:
            f.write(await file.read())

        file_size = os.path.getsize(os.path.join(UPLOAD_FOLDER, filename))
    
        if int(file_size) < max_file_size:
            upload_response, content_type = upload_to_aws(filename,valid_formats,original_filename,datastore_id)
            
            if upload_response:
                os.remove(os.path.join(UPLOAD_FOLDER,filename))
                document_id = DatastoresDocuments.create(type='file',name=original_filename,bytes=file_size,
                    tokens=0,meta={'url':f"{datastore_id}/{filename}"},datastore_id=record[0]['id'],user_id=user_data['user_id'],
                    workspace_id=user_data['workspace_id'],created=time.time()).id
                
                c_app.send_task(
                    "semantic.upload_file_vector",
                    kwargs={
                        'file':{
                            'name':upload_response,
                            'original_name': original_filename,
                            'mime_type':content_type,
                            'size':file_size,
                            'datastore_id':datastore_id
                        },
                        'user':user_data,
                        'document_id':document_id,
                        'datastore': record[0],
                        'metadata':json.loads(metadata) if metadata else {}
                    },
                    queue="semantic",
                )
                
                print('continue working')
                continue
            
            os.remove(os.path.join(UPLOAD_FOLDER,filename))
            errors.append({'status':403, 'text':f'File did not get uploaded - {original_filename}'})
            print('continue not uploaded')
            continue

        os.remove(os.path.join(UPLOAD_FOLDER,filename))
        errors.append({'status':403, 'text':f'File size is too big too upload - {original_filename}'})

    print(errors)
    if errors:
        raise HTTPException(errors[0]['status'], detail=errors[0]['text'])
    
    return {'status':'ok'}