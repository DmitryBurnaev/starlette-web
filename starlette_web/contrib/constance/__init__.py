from typing import Any, List, Dict

from starlette_web.common.http.exceptions import (
    NotSupportedError,
    BaseApplicationError,
    UnexpectedError,
)
from starlette_web.common.utils import import_string
from starlette_web.contrib.constance.backends.base import BaseConstanceBackend

from starlette_web.common.conf import settings


class LazyConstance:
    _backend: BaseConstanceBackend
    _is_setup: bool

    def __init__(self):
        self._is_setup = False

    async def get(self, key: str) -> Any:
        self._setup()

        if key not in settings.CONSTANCE_CONFIG:
            raise NotSupportedError

        value = await self._backend.get(key)
        return self._postprocess_value(key, value)

    async def set(self, key: str, value: Any) -> None:
        self._setup()

        if key not in settings.CONSTANCE_CONFIG:
            raise NotSupportedError

        expected_type = settings.CONSTANCE_CONFIG[key][2]
        if type(value) != expected_type:
            try:
                # This is for cases like int-float, str-int and such
                value = expected_type(value)
            except (TypeError, ValueError) as exc:
                raise NotSupportedError(details=str(exc))
            except Exception as exc:
                # I.e. if we try to pass datetime to uuid value, which causes OverflowError
                raise UnexpectedError(details=str(exc))

        await self._backend.set(key, value)

    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        self._setup()

        if not keys:
            return {}

        for key in keys:
            if key not in settings.CONSTANCE_CONFIG:
                raise NotSupportedError

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
            _backend_kls = import_string(settings.CONSTANCE_BACKEND)
        except (AttributeError, BaseApplicationError):
            _backend_kls = None

        if _backend_kls:
            self._backend = _backend_kls()

        self._is_setup = True


config = LazyConstance()
