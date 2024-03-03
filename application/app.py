import time
import openai
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from application.helpers.extensions import load_extensions
from .helpers.core import load_environment, send_log_slack_message
from .router import datastore, health, semantic, upload, chat, message, apps, documents, embed, crawler


def register_routers(app):
    """Register app routers."""
    app.include_router(health.router,prefix='/health')
    app.include_router(datastore.router,prefix='/v1')
    app.include_router(semantic.router,prefix='/v1')
    app.include_router(upload.router,prefix='/v1')
    app.include_router(chat.router,prefix='/v1')
    app.include_router(message.router,prefix='/v1')
    app.include_router(crawler.router,prefix='/v1')
    app.include_router(embed.router,prefix='/v1')
    app.include_router(documents.router,prefix='/v1')
    app.include_router(apps.router,prefix='/v1')
    
    
def create_app() -> FastAPI:
    """App factory. """
    app = FastAPI(title='LLM API')
    load_environment()
    load_extensions(app)
    register_routers(app)

    return app


app = create_app()


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    start = time.time()
    response = JSONResponse({'status':'error','error':{'message':'Internal server error'}},
         status_code=500)
    
    try:
        response = await call_next(request)
    
    except BaseException:
        print(traceback.format_exc())
        send_log_slack_message(traceback.format_exc())
        return response
        

    end = time.time()
    print(f'took {end-start}')

    return response

