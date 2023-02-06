from typing import Dict, Any, List

from sqlalchemy.orm import sessionmaker

from starlette_web.common.database import make_session_maker
from starlette_web.contrib.constance.backends.base import BaseConstanceBackend
from starlette_web.contrib.constance.backends.database.models import Constance


class DatabaseBackend(BaseConstanceBackend):
    session_maker: sessionmaker

    def __init__(self):
        super().__init__()
        # Disable connection pooling to avoid creating persistent open connections
        self.session_maker = make_session_maker(use_pool=False)

    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        async with self.session_maker() as session:
            constants = (await Constance.async_filter(db_session=session)).all()
            values = {key: self.empty for key in keys}
            values = {
                **values,
                **{
                    constant.key: self._preprocess_response(constant.value)
                    for constant in constants
                },
            }
            return values

    async def get(self, key: str) -> Any:
        async with self.session_maker() as session:
            val = await Constance.async_get(db_session=session, key=key)
            return self._preprocess_response(val.value if val else None)

    async def set(self, key: str, value: Any) -> None:
        async with self.session_maker() as session:
            await Constance.async_create_or_update(
                db_session=session,
                filter_kwargs={"key": key},
                update_data={"value": self.serializer.serialize(value)},
                db_commit=True,
            )
