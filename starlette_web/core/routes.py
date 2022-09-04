from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from starlette_web.common.conf import settings
from starlette_web.contrib.apispec.routes import routes as apispec_routes
from starlette_web.contrib.auth.routes import routes as auth_routes
from starlette_web.tests.views import HealthCheckAPIView, SentryCheckAPIView


# TODO: split auth and api
routes = [
    Mount("/api", routes=auth_routes),
    Mount("/openapi", routes=apispec_routes),
    Mount('/static', app=StaticFiles(directory=settings.STATIC["ROOT_DIR"]), name="static"),

    Route("/health_check/", HealthCheckAPIView),
    Route("/sentry_check/", SentryCheckAPIView),
]
