from fastapi.exceptions import HTTPException
from models import ApiKeys

def check_auth(headers):
    api_token = headers.get('x-api-key')
    
    if not api_token:
        raise HTTPException(401, 'No API Key')
    
    record = ApiKeys.select(ApiKeys.id,ApiKeys.key,ApiKeys.workspace_id, 
            ApiKeys.user_id,ApiKeys.is_internal).where(ApiKeys.key==api_token,ApiKeys.status == 1).dicts()
    
    if not record:
        raise HTTPException(401, 'Invalid API Key')
    
    return record[0]