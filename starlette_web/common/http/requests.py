from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request


# TODO: Maybe rename class ?
class PRequest(Request):
    db_session: Optional[AsyncSession] = None
