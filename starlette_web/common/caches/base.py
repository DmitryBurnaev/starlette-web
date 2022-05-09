from typing import Type, Any, Optional, Dict, Sequence, AsyncContextManager, List

from starlette_web.common.utils import Singleton
from starlette_web.common.utils.serializers import BaseSerializer, PickleSerializer


class CacheError(Exception):
    pass


class CacheLockError(CacheError):
    pass


class BaseCache(metaclass=Singleton):
    serializer_class: Type[BaseSerializer] = PickleSerializer
    serializer: BaseSerializer

    def __init__(self, params: Dict[str, Any]):
        self.serializer = self.serializer_class()

    async def async_get(self, key: str) -> Any:
        raise NotImplementedError

    async def async_set(self, key: str, value: Any, timeout: Optional[int] = 120) -> None:
        raise NotImplementedError

    async def async_delete(self, key: str) -> None:
        raise NotImplementedError

    async def keys(self, pattern: str) -> List[str]:
        raise NotImplementedError

    async def async_has_key(self, key: str) -> bool:
        return (await self.keys(key)) is not None

    async def async_get_many(self, keys: Sequence[str]) -> Dict[str, Any]:
        result = dict()
        for key in keys:
            result[key] = await self.async_get(key)
        return result

    async def async_set_many(self, data: Dict[str, Any], timeout: Optional[int] = 120) -> None:
        for key, value in data.items():
            await self.async_set(key, value, timeout=timeout)

    async def async_delete_many(self, keys: Sequence[str]) -> None:
        for key in keys:
            await self.async_delete(key)

    async def async_clear(self) -> None:
        raise NotImplementedError

    def lock(self, lock_name: str, blocking_interval: int) -> AsyncContextManager:
        raise NotImplementedError
