import os
import json
from fastapi import APIRouter, HTTPException, Request
from application.models.messages import MessageResponse
from application.models.sources import SourcesItemResponse
from application.utils.auth import check_auth
from models import ChatMessages, ChatApps, ChatSessions

router = APIRouter(prefix='/messages')


@router.get('/{app_id}/{session_id}',tags=['Messages'],name='List')
def get_messages(request: Request, app_id: str, session_id: str) -> MessageResponse:
    user_data = check_auth(request.headers)
    
    workspace_id = user_data['workspace_id']
    
    app_record = ChatApps.select(ChatApps.id).where(ChatApps.pid==app_id,
            ChatApps.workspace_id==workspace_id,ChatApps.type=='chat').dicts()

    if not app_record:
        raise HTTPException(404, 'Chat app not found')
    
    app_record = app_record[0]
    session_record = ChatSessions.select().where(ChatSessions.session_pid==session_id,
        ChatSessions.app_id==app_record['id'],ChatSessions.workspace_id==workspace_id).dicts()
    
    if not session_record:
        raise HTTPException(404, 'Session not found')

    messages = ChatMessages.select(ChatMessages.pid.alias('id'), ChatMessages.message, ChatMessages.type,
        ChatMessages.created).where(ChatMessages.session_id == session_record[0]['id']).order_by(ChatMessages.id.desc()).dicts()

    messages = list(messages)
    
    messages.reverse()

    return {
        "messages":messages
    }


@router.get('/{message_id}',description='Get Sources',tags=['Messages'],name='Message Sources')
def get_message_sources(message_id: str, request: Request) -> list[SourcesItemResponse]:
    check_auth(request.headers)
    
    record = ChatMessages.select().where(ChatMessages.pid == message_id).dicts()
    if not record:
        raise HTTPException(404, 'Message not found')
    
    cdn_url = json.loads(os.environ['app'])['aws']['s3']
    sources = record[0]['sources']
    for source in sources:
        if source['type'] in ['file','text']:
            source['url'] = cdn_url + source['url']
    
    return sources
    