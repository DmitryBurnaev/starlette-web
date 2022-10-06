import logging
import logging.config
from typing import List, Union, Dict, Callable, Type, TypeVar

from sqlalchemy.orm import sessionmaker
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Route, Mount, WebSocketRoute
from webargs_starlette import WebargsHTTPException

from starlette_web.common.caches import caches
from starlette_web.common.conf import settings
from starlette_web.common.database import make_session_maker
from starlette_web.common.http.exception_handlers import (
    BaseApplicationErrorHandler,
    WebargsHTTPExceptionHandler,
)
from starlette_web.common.http.renderers import BaseRenderer
from starlette_web.common.http.requests import PRequest
from starlette_web.common.http.exceptions import BaseApplicationError
from starlette_web.common.utils import import_string


__APPLICATION = None
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

    def pre_app_init(self) -> None:
        """
        Extra actions before app's initialization (can be overridden)
        """
        pass

    def post_app_init(self, app: AppClass) -> None:
        """
        Extra actions after app's initialization (can be overridden)
        """
        pass

    def get_debug(self) -> bool:
        return settings.APP_DEBUG

    def get_middleware(self) -> List[Middleware]:
        return []

    def get_routes(self) -> List[Union[WebSocketRoute, Route, Mount]]:
        return import_string(settings.ROUTES)

    def get_exception_handlers(self) -> Dict[Type[Exception], ExceptionHandlerType]:
        return {
            BaseApplicationError: BaseApplicationErrorHandler(),
            WebargsHTTPException: WebargsHTTPExceptionHandler(),
        }

    def get_app(self) -> AppClass:
        object.__getattribute__(settings, "_setup")()
        self.pre_app_init()

        app = self.app_class(
            routes=self.get_routes(),
            exception_handlers=self.get_exception_handlers(),
            debug=self.get_debug(),
            middleware=self.get_middleware(),
        )

        self._setup_logging(app)
        self._setup_caches(app)
        self._setup_constance(app)

        self.post_app_init(app)
        return app

    def _setup_logging(self, app: AppClass):
        logging.config.dictConfig(settings.LOGGING)

    def _setup_caches(self, app: AppClass):
        if hasattr(settings, "CACHES"):
            for conn_name in settings.CACHES:
                _ = caches[conn_name]

    def _setup_constance(self, app: AppClass):
        from starlette_web.contrib.constance import config

        config._setup()

        try:
            if settings.CONSTANCE_BACKEND:
                backend = config._backend
                if getattr(backend, "app", None) is None:
                    backend.app = app
        except (AttributeError, BaseApplicationError):
            pass


def get_app() -> AppClass:
    global __APPLICATION
    if __APPLICATION is None:
        StarletteApplication = import_string(settings.APPLICATION_CLASS)
        __APPLICATION = StarletteApplication().get_app()
    return __APPLICATION
