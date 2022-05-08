import logging
import logging.config
from typing import List, Union, Dict, Callable, Type, TypeVar

import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.logging import LoggingIntegration
from sqlalchemy.orm import sessionmaker
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Route, Mount, WebSocketRoute
from webargs_starlette import WebargsHTTPException

from starlette_web.common.database import make_session_maker
from starlette_web.common.http.exception_handlers import (
    BaseApplicationErrorHandler,
    WebargsHTTPExceptionHandler,
)
from starlette_web.common.http.renderers import BaseRenderer
from starlette_web.common.http.requests import PRequest
from starlette_web.core import settings
from starlette_web.core.routes import routes as core_routes
from starlette_web.common.http.exceptions import BaseApplicationError


AppClass = TypeVar("AppClass", bound=Starlette)
ExceptionHandlerType = Callable[[PRequest, Exception], BaseRenderer]


class WebApp(Starlette):
    """Simple adaptation of Starlette APP. Small addons here."""

    session_maker: sessionmaker

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_maker = make_session_maker()


class BaseStarletteApplication:
    app_class: AppClass = WebApp

    def pre_app_init(self):
        """
        Extra actions before app's initialization (can be overridden)
        """
        pass

    def post_app_init(self, app: AppClass):
        """
        Extra actions after app's initialization (can be overridden)
        """
        # TODO: remove logging to Sentry
        logging.config.dictConfig(settings.LOGGING)

        if settings.SENTRY_DSN:
            logging_integration = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
            sentry_sdk.init(settings.SENTRY_DSN, integrations=[logging_integration])

    @property
    def debug(self):
        return settings.APP_DEBUG

    @property
    def middleware(self):
        # TODO: remove sentry middleware
        return [Middleware(SentryAsgiMiddleware)]

    @property
    def routes(self) -> List[Union[WebSocketRoute, Route, Mount]]:
        # TODO: instead determine main routes.py file from lazy settings
        return core_routes

    @property
    def exception_handlers(self) -> Dict[Type[Exception], ExceptionHandlerType]:
        return {
            BaseApplicationError: BaseApplicationErrorHandler(),
            WebargsHTTPException: WebargsHTTPExceptionHandler(),
        }

    def get_app(self) -> AppClass:
        self.pre_app_init()

        app = self.app_class(
            routes=self.routes,
            exception_handlers=self.exception_handlers,
            debug=self.debug,
            middleware=self.middleware,
        )

        self.post_app_init(app)
        return app
