from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.types import Scope

from starlette_web.common.authorization.base_user import BaseUserMixin, AnonymousUser
from starlette_web.common.ws.requests import WSRequest
from starlette_web.common.http.requests import PRequest


class BaseAuthenticationBackend:
    openapi_spec = None
    openapi_name = "Base"

    def __init__(self, request: PRequest | WSRequest, scope: Scope):
        self.request: PRequest | WSRequest = request
        self.db_session: Optional[AsyncSession] = self.request.db_session
        self.scope: Scope = scope

    async def authenticate(self) -> BaseUserMixin:
        raise NotImplementedError


class NoAuthenticationBackend(BaseAuthenticationBackend):
    openapi_name = "NoAuth"

    async def authenticate(self) -> BaseUserMixin:
        return AnonymousUser()
