from typing import Optional, List, Any

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette_admin.contrib.sqla.view import ModelView as BaseModelView

from starlette_web.contrib.auth.models import UserSession, UserInvite


class ModelView(BaseModelView):
    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        session: AsyncSession = request.state.session
        objs = await self.find_by_pks(request, pks)

        async with session.begin_nested():
            for obj in objs:
                await session.delete(obj)

        await session.commit()
        return len(objs)

    async def delete_cascade(self, request: Request, pks: List[Any]) -> Optional[int]:
        session: AsyncSession = request.state.session
        objs = await self.find_by_pks(request, pks)

        async with session.begin_nested():
            for obj in objs:
                await UserSession.async_delete(
                    db_session=session,
                    filter_kwargs={"user_id": obj.id},
                )
                await UserInvite.async_delete(
                    db_session=session,
                    filter_kwargs={"user_id": obj.id},
                )
                await session.delete(obj)

        await session.commit()
        return len(objs)
