from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import HTTPConnection
from starlette.types import Scope

from starlette_web.common.authorization.base_user import BaseUserMixin, AnonymousUser


class BaseAuthenticationBackend:
    openapi_spec = None
    openapi_name = "Base"

    def __init__(self, request: HTTPConnection, scope: Scope):
        self.request: HTTPConnection = request
        self.db_session: Optional[AsyncSession] = self.request.state.db_session
        self.scope: Scope = scope

    async def authenticate(self, **kwargs) -> BaseUserMixin:
        raise NotImplementedError


class NoAuthenticationBackend(BaseAuthenticationBackend):
    openapi_name = "NoAuth"

    async def authenticate(self, **kwargs) -> BaseUserMixin:
        return AnonymousUser()
