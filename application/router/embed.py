import time
from fastapi import APIRouter, Request
from application.models.embed import EmbedRequest, EmbedResponse
from application.utils.auth import check_auth
from application.utils.cache import Embeddingcache
from application.utils.create_embed import create_embedding

router = APIRouter()

models = ['embedding-english-v1', 'embedding-multi-v1']

def embed_internal(input, model, headers):
    from project.tasks import embedding_usage

    user_data = check_auth(headers)
    arguments = EmbedRequest.parse_obj({'input':input, 'model':model})

    cached = Embeddingcache.get_cache(arguments)
    print(f'cache {bool(cached)}')
    
    if not cached:
        resp, token = create_embedding(arguments.input, arguments.model)
        Embeddingcache.set_cache(arguments, {'data':resp, 'usage': token})
        embedding_usage.apply_async(kwargs={'user':user_data, 'internal_api':True, 'model':arguments.model, 'token': token, 'text': arguments.input})

    else:
        resp  = cached['data']
        token = cached['usage']

    for i in resp:
        print(i['embedding'][:2])
            
    return {
        "object": "list",
        "data":resp,
        'model':arguments.model,
        "usage": {
            "prompt_tokens": token,
            "total_tokens": token
        }
    }

@router.post('/embeddings',tags=['Embedding'])
def embed_text(request: Request, arguments: EmbedRequest) -> EmbedResponse:
    from project.tasks import embedding_usage

    user_data = check_auth(request.headers)
    cached = Embeddingcache.get_cache(arguments)
    print(f'cache {bool(cached)}')

    if not cached:
        resp, token = create_embedding(arguments.input, arguments.model)
        Embeddingcache.set_cache(arguments, {'data':resp, 'usage': token})
        embedding_usage.apply_async(kwargs={'user':user_data, 'internal_api':False, 'model':arguments.model, 'token': token, 'text': arguments.input})

    else:
        resp  = cached['data']
        token = cached['usage']

    for i in resp:
        print(i['embedding'][:2])
            
    return {
        "object": "list",
        "data":resp,
        'model':arguments.model,
        "usage": {
            "prompt_tokens": token,
            "total_tokens": token
        }
    }
