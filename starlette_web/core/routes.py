from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles

from starlette_web.common.conf import settings
from starlette_web.contrib.apispec.routes import routes as apispec_routes
from starlette_web.contrib.auth.routes import routes as auth_routes
from starlette_web.contrib.admin import admin, AdminMount
from starlette_web.tests.views import (
    HealthCheckAPIView,
    SentryCheckAPIView,
    BaseWebsocketTestEndpoint,
    CancellationWebsocketTestEndpoint,
    AuthenticationWebsocketTestEndpoint,
    FinitePeriodicTaskWebsocketTestEndpoint,
    InfinitePeriodicTaskWebsocketTestEndpoint,
)


# TODO: split auth and api
routes = [
    Mount("/api", routes=auth_routes),
    Mount("/openapi", routes=apispec_routes),
    AdminMount("/admin", app=admin.get_app(), name="admin"),
    Mount("/static", app=StaticFiles(directory=settings.STATIC["ROOT_DIR"]), name="static"),
    Route("/health_check/", HealthCheckAPIView),
    Route("/sentry_check/", SentryCheckAPIView),
    WebSocketRoute("/ws/test_websocket_base", BaseWebsocketTestEndpoint),
    WebSocketRoute("/ws/test_websocket_cancel", CancellationWebsocketTestEndpoint),
    WebSocketRoute("/ws/test_websocket_auth", AuthenticationWebsocketTestEndpoint),
    WebSocketRoute("/ws/test_websocket_finite_periodic", FinitePeriodicTaskWebsocketTestEndpoint),
    WebSocketRoute(
        "/ws/test_websocket_infinite_periodic", InfinitePeriodicTaskWebsocketTestEndpoint
    ),
]
