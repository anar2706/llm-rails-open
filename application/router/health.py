from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import Response
from application.utils.auth import check_auth


router = APIRouter()


@router.get("",tags=['Health'])
async def healthcheck(request: Request):
    return Response(status_code=200)
