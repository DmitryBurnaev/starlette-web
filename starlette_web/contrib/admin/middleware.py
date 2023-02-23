from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from starlette_web.common.database.session_maker import make_session_maker


class DBSessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self.session_maker = make_session_maker(use_pool=False)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        async with self.session_maker() as session:
            request.state.session = session
            response = await call_next(request)
            del request.state.session
            return response
