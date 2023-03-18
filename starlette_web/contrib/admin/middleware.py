import datetime
import jwt
from functools import partial

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.datastructures import MutableHeaders
from starlette.requests import HTTPConnection, Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from starlette.responses import Response

from starlette_web.common.conf import settings
from starlette_web.common.database.session_maker import make_session_maker
from starlette_web.contrib.auth.backend import SessionJWTAuthenticationBackend
from starlette_web.contrib.auth.models import UserSession
from starlette_web.contrib.auth.utils import decode_jwt


class DBSessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.session_maker = make_session_maker(use_pool=False)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        async with self.session_maker() as session:
            try:
                request.state.session = session
                request.state.db_session = session
                response = await call_next(request)
                return response
            finally:
                del request.state.session
                del request.state.db_session


class AdminSessionMiddleware:
    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        self.app = app
        self.session_cookie = SessionJWTAuthenticationBackend.cookie_name
        self.max_age = settings.AUTH_JWT_REFRESH_EXPIRES_IN
        self.path = "/"
        self.session_maker = make_session_maker(use_pool=False)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope)
        initial_session_was_empty = True

        if self.session_cookie in connection.cookies:
            try:
                token = connection.cookies[self.session_cookie]
                scope["session"] = decode_jwt(token)
                scope["session"]["token"] = token
                initial_session_was_empty = False
            except jwt.PyJWTError:
                scope["session"] = {}
        else:
            scope["session"] = {}

        send_wrapper = partial(
            self.send_wrapper,
            scope=scope,
            send=send,
            initial_session_was_empty=initial_session_was_empty,
        )
        await self.app(scope, receive, send_wrapper)

    async def send_wrapper(
        self,
        message: Message,
        scope: Scope,
        send: Send,
        initial_session_was_empty: bool = True,
    ) -> None:
        security_flags = "httponly; samesite=lax"
        if scope.get("scheme") == "https":
            security_flags += "; secure"

        if message["type"] == "http.response.start":
            if scope.get("session", {}) and scope["session"].get("token"):
                async with self.session_maker() as db_session:
                    user_session = await UserSession.async_get(
                        db_session=db_session,
                        refresh_token=scope["session"]["token"],
                    )

                if user_session and not user_session.is_persistent:
                    expires = ""
                elif "exp" in scope["session"]:
                    expires = datetime.datetime.utcfromtimestamp(scope["session"]["exp"])
                    expires = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
                    expires = f"expires={expires}; "
                elif self.max_age:
                    expires = f"Max-Age={self.max_age}; "
                else:
                    expires = ""

                # We have session data to persist.
                headers = MutableHeaders(scope=message)
                header_value = "{session_cookie}={data}; path={path}; {expires}{security_flags}".format(  # noqa E501
                    session_cookie=self.session_cookie,
                    data=scope["session"]["token"],
                    path=self.path,
                    expires=expires,
                    security_flags=security_flags,
                )
                headers.append("Set-Cookie", header_value)
            elif not initial_session_was_empty:
                # The session has been cleared.
                headers = MutableHeaders(scope=message)
                header_value = "{session_cookie}={data}; path={path}; {expires}{security_flags}".format(  # noqa E501
                    session_cookie=self.session_cookie,
                    data="null",
                    path=self.path,
                    expires="expires=Thu, 01 Jan 1970 00:00:00 GMT; ",
                    security_flags=security_flags,
                )
                headers.append("Set-Cookie", header_value)

        await send(message)
