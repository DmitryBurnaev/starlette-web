from starlette.routing import Mount, Route

from starlette_web.contrib.auth.routes import routes as auth_routes
from starlette_web.tests.views import HealthCheckAPIView, SentryCheckAPIView


routes = [
    Mount("/api", routes=auth_routes),
    Route("/health_check/", HealthCheckAPIView),
    Route("/sentry_check/", SentryCheckAPIView),
]
