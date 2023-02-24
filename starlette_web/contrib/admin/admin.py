from typing import Optional, Sequence, Any

from sqlalchemy.exc import IntegrityError
from starlette.applications import Starlette
from starlette.datastructures import URLPath
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount
from starlette_admin.auth import AuthProvider
from starlette_admin.base import BaseAdmin
from starlette_admin.views import CustomView
from starlette_admin.exceptions import StarletteAdminException

from starlette_web.common.conf import settings
from starlette_web.contrib.admin.middleware import DBSessionMiddleware
from starlette_web.common.utils import urljoin


class AdminMount(Mount):
    def __init__(self, path, **kwargs):
        super().__init__(path, **kwargs)
        self._base_app.state.ROUTE_NAME = self.name

    # starlette_admin is not a built-in module of starlette_web,
    # so it requires specific workaround for static files
    def url_path_for(self, name: str, **path_params: Any) -> URLPath:
        if (name == self.name + ":statics") and ("path" in path_params):
            path = urljoin(settings.STATIC["URL"], "admin", path_params["path"])
            return URLPath(path=path, protocol="http")
        return super().url_path_for(name, **path_params)


class Admin(BaseAdmin):
    def __init__(
        self,
        title: str = "Admin",
        logo_url: Optional[str] = None,
        login_logo_url: Optional[str] = None,
        index_view: Optional[CustomView] = None,
        auth_provider: Optional[AuthProvider] = None,
        middlewares: Optional[Sequence[Middleware]] = None,
    ) -> None:
        super().__init__(
            title=title,
            base_url="/admin",
            route_name="admin",
            logo_url=logo_url,
            login_logo_url=login_logo_url,
            templates_dir=settings.TEMPLATES["ROOT_DIR"],
            statics_dir=None,
            index_view=index_view,
            auth_provider=auth_provider,
            middlewares=middlewares,
            debug=settings.APP_DEBUG,
        )
        self.middlewares = [] if self.middlewares is None else list(self.middlewares)
        # TODO: support CSRF protection
        self.middlewares = [
            Middleware(DBSessionMiddleware),
        ] + self.middlewares

        # Remove static files from starlette_admin routing,
        # it is handled differently
        self.routes = [route for route in self.routes if type(route) != Mount]

    def get_app(self) -> Starlette:
        for route in self.routes:
            if hasattr(route, "include_in_schema"):
                route.include_in_schema = False

        admin_app = Starlette(
            routes=self.routes,
            middleware=self.middlewares,
            debug=self.debug,
            exception_handlers={
                HTTPException: self._render_error,
                StarletteAdminException: self._render_error,
                IntegrityError: self._render_error,
            },
        )
        return admin_app

    async def _render_error(
        self,
        request: Request,
        exc: Exception = HTTPException(status_code=500),  # noqa: B008
    ) -> Response:

        try:
            _ = exc.status_code
            _ = exc.detail
        except AttributeError:
            exc.status_code = 500
            exc.detail = str(exc)

        return self.templates.TemplateResponse(
            "error.html",
            {"request": request, "exc": exc},
            status_code=exc.status_code,
        )
