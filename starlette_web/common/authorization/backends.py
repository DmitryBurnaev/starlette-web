from sqlalchemy.ext.asyncio import AsyncSession

from starlette_web.common.authorization.base_user import BaseUser, AnonymousUser


class BaseAuthenticationBackend:
    def __init__(self, request):
        self.request = request
        self.db_session: AsyncSession = request.db_session

    async def authenticate(self) -> BaseUser:
        raise NotImplementedError


class NoAuthenticationBackend(BaseAuthenticationBackend):
    async def authenticate(self) -> BaseUser:
        return AnonymousUser()
