from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request


class PRequest(Request):
    user_session_id: str
    db_session: AsyncSession
