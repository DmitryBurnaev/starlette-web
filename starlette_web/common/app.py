import inspect
import logging
import logging.config
from typing import List, Union, Dict, Callable, Type, TypeVar

from sqlalchemy.orm import sessionmaker
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.routing import Route, Mount, WebSocketRoute
from webargs_starlette import WebargsHTTPException

from starlette_web.common.caches import caches
from starlette_web.common.conf import settings
from starlette_web.common.conf.app_manager import app_manager
from starlette_web.common.database import make_session_maker
from starlette_web.common.http.exception_handlers import (
    BaseApplicationErrorHandler,
    WebargsHTTPExceptionHandler,
)
from starlette_web.common.http.renderers import BaseRenderer
from starlette_web.common.http.exceptions import BaseApplicationError
from starlette_web.common.utils import import_string


AppClass = TypeVar("AppClass", bound=Starlette)
ExceptionHandlerType = Callable[[Request, Exception], BaseRenderer]


class WebApp(Starlette):
    """Simple adaptation of Starlette APP. Small addons here."""

    session_maker: sessionmaker

    def __init__(self, *args, **kwargs):
        use_pool = kwargs.pop("use_pool", True)

        allowed_params = inspect.getfullargspec(Starlette.__init__).args
        starlette_init_kwargs = {
            key: value for key, value in kwargs.items() if key in allowed_params
        }
        super().__init__(*args, **starlette_init_kwargs)

        self.session_maker = make_session_maker(use_pool=use_pool)


class BaseStarletteApplication:
    app_class: AppClass = WebApp

    def __init__(self, **kwargs):
        self.run_checks = kwargs.get("run_checks", True)
        self._event_handlers = []

    def pre_app_init(self) -> None:
        """
        Extra actions before app's initialization (can be overridden)
        """
        app_manager.initialize_apps()
        if self.run_checks:
            app_manager.run_apps_checks()

    def post_app_init(self, app: AppClass) -> None:
        """
        Extra actions after app's initialization (can be overridden)
        """
        pass

    def get_debug(self) -> bool:
        return settings.APP_DEBUG

    def get_middlewares(self) -> List[Middleware]:
        return settings.MIDDLEWARES

    def get_routes(self) -> List[Union[WebSocketRoute, Route, Mount]]:
        return import_string(settings.ROUTES)

    def get_exception_handlers(self) -> Dict[Type[Exception], ExceptionHandlerType]:
        return {
            BaseApplicationError: BaseApplicationErrorHandler(),
            WebargsHTTPException: WebargsHTTPExceptionHandler(),
        }

    def get_app(self, **kwargs) -> AppClass:
        object.__getattribute__(settings, "_setup")()
        self.pre_app_init()

        app = self.app_class(
            routes=self.get_routes(),
            exception_handlers=self.get_exception_handlers(),
            debug=self.get_debug(),
            middleware=self.get_middlewares(),
            **kwargs,
        )

        self._setup_logging(app)
        self._setup_caches(app)
        self._manage_event_handlers(app)

        self.post_app_init(app)
        return app

    def _setup_logging(self, app: AppClass):
        logging.config.dictConfig(settings.LOGGING)

    def _setup_caches(self, app: AppClass):
        for conn_name in settings.CACHES:
            _ = caches[conn_name]

    def _manage_event_handlers(self, app: AppClass):
        shutdown_handlers = []

        for startup_handler, shutdown_handler in self._event_handlers:
            app.add_event_handler("startup", startup_handler)
            shutdown_handlers.append(shutdown_handler)

        # Take care of nesting event handlers, which may provide
        # context-manager cancel scopes, which must be properly nested LIFO
        for shutdown_handler in shutdown_handlers[::-1]:
            app.add_event_handler("shutdown", shutdown_handler)


def get_app(**kwargs) -> AppClass:
    StarletteApplication = import_string(settings.APPLICATION_CLASS)
    run_checks = kwargs.pop("run_checks_on_startup", True)
    return StarletteApplication(run_checks=run_checks).get_app(**kwargs)
