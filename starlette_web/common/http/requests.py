from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request


# TODO: Maybe rename class ?
class PRequest(Request):
    # TODO: move user_session_id outside of definition of PRequest
    user_session_id: str
    db_session: AsyncSession
