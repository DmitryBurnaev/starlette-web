from apispec import APISpec

from starlette_web.common.conf import settings
from starlette_web.common.http.base_endpoint import BaseHTTPEndpoint
from starlette_web.common.http.renderers import JSONRenderer
from starlette_web.common.http.requests import PRequest
from starlette_web.common.http.responses import TemplateResponse
from starlette_web.common.utils import urljoin
from starlette_web.contrib.apispec.introspection import APISpecSchemaGenerator
from starlette_web.contrib.apispec.marshmallow import StarletteWebMarshmallowPlugin


api_spec = APISpec(
    **settings.APISPEC["CONFIG"],
    plugins=[StarletteWebMarshmallowPlugin()],
)


schemas = APISpecSchemaGenerator(api_spec)


# TODO: think about managing permissions
class OpenApiView(BaseHTTPEndpoint):
    auth_backend = None
    permission_classes = []

    async def get(self, request: PRequest):
        routes = request.app.routes
        return JSONRenderer(schemas.get_schema(routes))


# TODO: think about managing permissions
class RedocView(BaseHTTPEndpoint):
    auth_backend = None
    permission_classes = []

    async def get(self, request: PRequest):
        return TemplateResponse(
            "apispec/redoc.html",
            context={
                # TODO: dynamically obtain url for endpoint or allow configuring
                "REDOC_SPEC_URL": "/openapi/schema/",
                "REDOC_JS_URL": urljoin(settings.STATIC["URL"], "apispec", "redoc.js"),
                "REDOC_TITLE": "OPENAPI documentation",
                "request": request,
            },
        )
