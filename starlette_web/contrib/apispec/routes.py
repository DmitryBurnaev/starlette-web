from starlette.routing import Route, Mount
from starlette_web.contrib.apispec import views


routes = [
    Mount(
        "/openapi",
        routes=[
            Route("/redoc/", views.RedocView, include_in_schema=False),
            Route("/schema/", views.OpenApiView, include_in_schema=False),
        ],
    )
]
