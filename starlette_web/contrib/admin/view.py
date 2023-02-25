from typing import Optional, List, Any

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette_admin.contrib.sqla.view import ModelView as BaseModelView


class ModelView(BaseModelView):
    async def delete(self, request: Request, pks: List[Any]) -> Optional[int]:
        session: AsyncSession = request.state.session
        objs = await self.find_by_pks(request, pks)

        async with session.begin_nested():
            for obj in objs:
                await session.delete(obj)

        await session.commit()
        return len(objs)
