from starlette.routing import Route

from common.views import HealthCheckAPIView, SentryCheckAPIView


routes = [
    Route("/health_check/", HealthCheckAPIView),
    Route("/sentry_check/", SentryCheckAPIView),
]
