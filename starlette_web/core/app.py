import logging
import logging.config

import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.logging import LoggingIntegration
from sqlalchemy.orm import sessionmaker
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Route
from webargs_starlette import WebargsHTTPException

from starlette_web.common.typing import AppClass
from starlette_web.common.db_utils import make_session_maker
from starlette_web.core import settings
from starlette_web.core.routes import routes as core_routes
from starlette_web.common.utils import custom_exception_handler
from starlette_web.common.http.exceptions import BaseApplicationError

exception_handlers = {
    BaseApplicationError: custom_exception_handler,
    WebargsHTTPException: custom_exception_handler,
}


class WebApp(Starlette):
    """Simple adaptation of Starlette APP. Small addons here."""

    session_maker: sessionmaker

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_maker = make_session_maker()


def get_app(app_class: AppClass = WebApp, routes: list[Route] = core_routes):
    app = app_class(
        routes=routes,
        exception_handlers=exception_handlers,
        debug=settings.APP_DEBUG,
        middleware=[Middleware(SentryAsgiMiddleware)],
    )
    logging.config.dictConfig(settings.LOGGING)
    if settings.SENTRY_DSN:
        logging_integration = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
        sentry_sdk.init(settings.SENTRY_DSN, integrations=[logging_integration])

    return app
