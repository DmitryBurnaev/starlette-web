from typing import Any, List, Dict

from starlette_web.common.http.exceptions import NotSupportedError, BaseApplicationError
from starlette_web.common.utils import import_string
from starlette_web.contrib.constance.backends.base import BaseConstanceBackend

from starlette_web.common.conf import settings


class LazyConstance:
    _backend: BaseConstanceBackend
    _is_setup: bool

    def __init__(self):
        self._is_setup = False

    async def get(self, key: str) -> Any:
        if not self._setup:
            self._setup()

        if key not in settings.CONSTANCE_CONFIG:
            raise NotSupportedError

        value = await self._backend.get(key)
        return self._postprocess_value(key, value)

    async def set(self, key: str, value: Any) -> None:
        if key not in settings.CONSTANCE_CONFIG:
            raise NotSupportedError

        expected_type = settings.CONSTANCE_CONFIG[key][2]
        if type(value) != expected_type:
            try:
                value = expected_type(value)
            except (TypeError, ValueError) as exc:
                raise NotSupportedError(details=str(exc))

        await self._backend.set(key, value)

    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        if not keys:
            return {}

        return_list = await self._backend.mget(keys)
        return {key: self._postprocess_value(key, value) for key, value in return_list.items()}

    def _postprocess_value(self, key, value):
        if key not in settings.CONSTANCE_CONFIG:
            raise NotSupportedError

        if value is self._backend.empty:
            return settings.CONSTANCE_CONFIG[key][0]

        return value

    def _setup(self) -> None:
        if self._is_setup:
            return

        try:
            self._backend = import_string(settings.CONSTANCE_BACKEND)()
            self._is_setup = True
        except (AttributeError, BaseApplicationError):
            pass


config = LazyConstance()
