from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.exceptions import HTTPException
from application.models.apps import AppItemResponse
from application.utils.auth import check_auth
from models import ChatApps

router = APIRouter(prefix='/apps')


@router.get("",tags=['Apps'],name='List')
def get_apps(request: Request) -> list[AppItemResponse]:
    user_data = check_auth(request.headers)
    
    chat_apps = ChatApps.select(ChatApps.pid.alias('id'),
        ChatApps.name,ChatApps.type,ChatApps.created,ChatApps.updated).where(ChatApps.workspace_id == user_data['workspace_id']).dicts()
    
    return list(chat_apps)


@router.get("/{app_id}",tags=['Apps'],name='Get')
def get_app_detail(app_id: str,request: Request) -> AppItemResponse:
    user_data = check_auth(request.headers)
    
    chat_apps = ChatApps.select(ChatApps.pid.alias('id'),
        ChatApps.name,ChatApps.type,ChatApps.created,ChatApps.updated).where(ChatApps.pid == app_id,
        ChatApps.workspace_id == user_data['workspace_id']).dicts()
    
    if not chat_apps:
        raise HTTPException(404, 'Chat app not found')
    
    return chat_apps[0]