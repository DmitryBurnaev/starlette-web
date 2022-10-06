from typing import Dict, Any, List

from starlette_web.contrib.constance.backends.base import BaseConstanceBackend
from starlette_web.contrib.constance.backends.database.models import Constance


class DatabaseBackend(BaseConstanceBackend):
    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        async with self.app.session_maker() as session:
            keys = await Constance.async_filter(db_session=session)
            values = {key.key: self._preprocess_response(key.value) for key in keys}
            return values

    async def get(self, key: str) -> Any:
        async with self.app.session_maker() as session:
            val = await Constance.async_get(db_session=session, key=key)
            return self._preprocess_response(val.value if val else None)

    async def set(self, key: str, value: Any) -> None:
        async with self.app.session_maker() as session:
            await Constance.async_create_or_update(
                db_session=session,
                filter_kwargs={"key": key},
                update_data={"value": self.serializer.serialize(value[0])},
                db_commit=True,
            )
