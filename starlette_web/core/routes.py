from starlette.routing import Mount, Route

from starlette_web.common.views import HealthCheckAPIView, SentryCheckAPIView
from starlette_web.auth.routes import routes as auth_routes

routes = [
    Mount("/api", routes=auth_routes),
    Route("/health_check/", HealthCheckAPIView),
    Route("/sentry_check/", SentryCheckAPIView),
]
