import logging

import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.logging import LoggingIntegration
from starlette.middleware import Middleware

from starlette_web.common.app import BaseStarletteApplication, AppClass, settings
from starlette_web.common.http.exceptions import ImproperlyConfigured


class TestStarletteApplication(BaseStarletteApplication):
    def post_app_init(self, app: AppClass):
        try:
            sentry_dsn = settings.SENTRY_DSN
        except ImproperlyConfigured:
            sentry_dsn = None

        if sentry_dsn:
            logging_integration = LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR,
            )
            sentry_sdk.init(sentry_dsn, integrations=[logging_integration])

    def get_middlewares(self):
        return super().get_middlewares() + [Middleware(SentryAsgiMiddleware)]
