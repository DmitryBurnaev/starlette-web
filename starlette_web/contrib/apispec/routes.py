from starlette.routing import Route
from starlette_web.contrib.apispec import views


routes = [
    Route("/redoc/", views.RedocView, include_in_schema=False),
    Route("/schema/", views.OpenApiView, include_in_schema=False, name="apispec_openapi_schema"),
]
