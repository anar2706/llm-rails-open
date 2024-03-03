from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from starlette.exceptions import HTTPException as StarletteHTTPException
from application.helpers.core import send_log_slack_message


def load_extensions(app):

    @app.on_event("startup")
    def startup():
        send_log_slack_message(f'LLM API has started')


    @app.on_event("shutdown")
    def shutdown():
        send_log_slack_message(f'!!!! LLM API has stopped!!!')
        
        # if not db.is_closed():
        #     db.close()


    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse({'status':'error','error':{'message':exc.detail}},exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        return JSONResponse({'status':'error','error':{'message':str(exc)}},400)


    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title="LLM API",
            version="1.0.0",
            description="LLM API",
            routes=app.routes
        )
        
        
        # openapi_schema["components"]["securitySchemes"] = {
        #     "X-API-KEY": {
        #         "type": "apiKey",
        #         "in": "header",
        #         "name": "X-API-KEY",
        #         "description": "Enter: **'&lt;Token&gt;'**, where Token is the access token"
        #     }
        # }

        # Get all routes where jwt_optional() or jwt_required
        openapi_schema['paths'].pop('/health',None)
        api_router = [route for route in app.routes if isinstance(route, APIRoute) if route.path not in ['/v1/count','/health']]

        for route in api_router:
            path = getattr(route, "path")
            endpoint = getattr(route,"endpoint")
            methods = [method.lower() for method in getattr(route, "methods")]

            # for method in methods:
            #     # access_token
            #     # if (
            #     #     re.search("jwt_required", inspect.getsource(endpoint)) or
            #     #     re.search("fresh_jwt_required", inspect.getsource(endpoint)) or
            #     #     re.search("jwt_optional", inspect.getsource(endpoint))
            #     # ):
            #     openapi_schema["paths"][path][method]["security"] = [
            #         {
            #             "X-API-KEY": []
            #         }
            #     ]

        app.openapi_schema = openapi_schema
        return app.openapi_schema


    app.openapi = custom_openapi
    # init_sentry()
    