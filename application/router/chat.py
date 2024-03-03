import os
import time
import json
import copy
from fastapi import APIRouter, HTTPException, Request
from application.models.chat import ConversationRequestBody
from application.utils.auth import check_auth
from application.utils.chat_data import ChatWithData
from application.utils.chat import Chat
from application.utils.general import generate_uuid
from models import Datastores, ChatSessions, ChatApps, ChatMessages

router = APIRouter(prefix='/chat/{app_id}')


@router.post('',tags=['Chat'],name='Chat')
def chat_message(app_id: str, request: Request, arguments: ConversationRequestBody):
    user_data = check_auth(request.headers)
    workspace_id = user_data['workspace_id']
    
    arguments = arguments.dict()
    print(arguments)
    app_record = ChatApps.select().where(ChatApps.pid==app_id,
            ChatApps.workspace_id==workspace_id,ChatApps.type=='chat').dicts()

    if not app_record:
        raise HTTPException(404, 'Chat app not found')
    
    app_record = app_record[0]
    schema     = app_record['datastore_id']
    text       = arguments['text']
    stream     = arguments['stream']
    session_id = arguments.get('session_id')
    text       = text.replace('"','\\"')
    
    internal_user_id  = arguments.get('internal_user_id')
    extnernal_user_id = arguments.get('user_id')
    extnernal_user_id = extnernal_user_id if extnernal_user_id else f"usr_{generate_uuid()}"
    datastore_record = Datastores.select(Datastores.id,Datastores.vector_id,Datastores.embedding_model).where(Datastores.id==schema).dicts()
    
    if session_id:
        chat_record = ChatSessions.select().where(ChatSessions.workspace_id==user_data['workspace_id'],
            ChatSessions.session_pid==session_id, ChatSessions.app_id == app_record['id'])
        
        if not chat_record:
            raise HTTPException(404, 'Chat session not found')
        
        chat_record = chat_record[0]
        chat_record.updated = time.time()
        chat_record.save()
    
    else:
        session_id = f"ses_{generate_uuid()}"
        chat_record = ChatSessions.create(user_pid=extnernal_user_id,internal_user_id=internal_user_id,
            workspace_id=user_data['workspace_id'],app_id=app_record['id'],
            session_pid=session_id,updated=time.time(),created=time.time())
    
    
    ChatMessages.create(pid=f"msg_{generate_uuid()}",session_id=chat_record.id,message=text,
        type=1,created=time.time())
    
    prompt = arguments['prompt'] if arguments.get('prompt') else app_record['prompt']
    message_pid = f"msg_{generate_uuid()}"
    bot_msg_record = ChatMessages.create(pid=message_pid,session_id=chat_record.id,
        message='',type=0,created=time.time())
    
    if not datastore_record:
        return Chat(text,stream,user_data, message_pid, bot_msg_record, 
            app_record['chat_model'], prompt, session_id).generate()
    
    datastore_record = datastore_record[0]
    chat_service = ChatWithData(datastore_record['vector_id'],datastore_record['embedding_model'],
        app_record['chat_model'], text, stream, user_data, message_pid, bot_msg_record, session_id,
        prompt, datastore_record['id'])
    
        
    docs = chat_service.search_documents()
    cdn_url = json.loads(os.environ['app'])['aws']['s3']
    sources = []
    
    for document in docs:
        doc = {
            'type':document.metadata.get('type'),
            'url':document.metadata['url'],
            'name':document.metadata['name'],
            'score':document.metadata.get('score')
        }
        
        sources.append(doc)
    
    bot_msg_record.sources = sources
    bot_msg_record.save()
    
    resp = chat_service.generate(docs)
    sources = copy.deepcopy(sources)
    for source in sources:
        if source['type'] in ['file','text']:
            source['url'] = cdn_url + source['url']
    
    if stream is False:
        resp['id'] = message_pid
        resp['session_id'] = session_id
        resp['docs'] = sources

    return resp