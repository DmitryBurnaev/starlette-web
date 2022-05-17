import logging

import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.logging import LoggingIntegration
from starlette.middleware import Middleware

from starlette_web.common.app import BaseStarletteApplication, AppClass
from starlette_web.core import settings


class TestStarletteApplication(BaseStarletteApplication):
    def post_app_init(self, app: AppClass):
        sentry_dsn = getattr(settings, "config", {}).get("SENTRY_DSN", None)

        if sentry_dsn:
            logging_integration = LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR,
            )
            sentry_sdk.init(sentry_dsn, integrations=[logging_integration])

    def get_middleware(self):
        return super().get_middleware() + [Middleware(SentryAsgiMiddleware)]
