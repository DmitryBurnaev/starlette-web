from typing import Sequence, Any, List, Dict, Type, Optional, AsyncContextManager

import aioredis

from starlette_web.common.caches.base import BaseCache, CacheError
from starlette_web.common.utils.async_utils import aclosing
from starlette_web.common.utils.serializers import BaseSerializer, JSONSerializer
from starlette_web.contrib.redis.redislock import RedisLock


def reraise_exception(func):
    async def wrapped(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except aioredis.exceptions.RedisError as exc:
            raise CacheError from exc

    return wrapped


class RedisCache(BaseCache):
    serializer_class: Type[BaseSerializer] = JSONSerializer
    redis = aioredis.Redis

    def __init__(self, params: Dict[str, Any]):
        super().__init__(params)
        self.redis = aioredis.Redis(
            host=params.get("host"),
            port=params.get("port"),
            db=params.get("db"),
            max_connections=params.get("max_connections", 32),
        )

    @reraise_exception
    async def async_get(self, key: str) -> Any:
        value = await self.redis.get(key)
        return self.serializer.deserialize(value)

    @reraise_exception
    async def async_set(self, key: str, value, timeout: Optional[int] = 120):
        await self.redis.set(key, self.serializer.serialize(value), ex=timeout)

    @reraise_exception
    async def async_delete(self, key: str) -> None:
        await self.redis.delete(key)

    @reraise_exception
    async def keys(self, pattern: str) -> List[str]:
        raise NotImplementedError

    @reraise_exception
    async def async_get_many(self, keys: Sequence[str]) -> Dict[str, Any]:
        result = dict()
        key_idx = 0

        async with aclosing(self.redis.mget(keys)) as async_generator:
            async for value in async_generator:
                result[keys[key_idx]] = self.serializer.deserialize(value)
                key_idx += 1

        return result

    @reraise_exception
    async def async_has_key(self, key: str) -> bool:
        return bool(await self.redis.exists(key))

    @reraise_exception
    async def async_set_many(self, data: Dict[str, Any], timeout: Optional[int] = 120) -> None:
        """
        Set multiple key-values with timeout.
        Note, that redis does not support setting timeout in MSET,
        which is why commands need to be wrapped with multi-exec block (provided by pipelines)
        """

        if len(data) < 2:
            await super().async_set_many(data, timeout)

        elif timeout is None:
            await self.redis.mset(
                {key: self.serializer.serialize(value) for key, value in data.items()}
            )

        else:
            async with aioredis.client.Pipeline(
                self.redis.connection_pool,
                response_callbacks={},
                transaction=True,
                shard_hint=None,
            ) as pipeline:
                for key, value in data.items():
                    pipeline.execute_command(
                        "SET",
                        key,
                        self.serializer.serialize(value),
                        "EX",
                        timeout,
                    )
                await pipeline.execute(raise_on_error=True)

    @reraise_exception
    async def async_delete_many(self, keys: Sequence[str]) -> None:
        await self.redis.delete(*keys)

    @reraise_exception
    async def async_clear(self) -> None:
        await self.redis.flushdb()

    def lock(self, name: str, blocking_timeout: int) -> AsyncContextManager:
        return self.redis.lock(
            name,
            timeout=blocking_timeout,
            blocking_timeout=blocking_timeout,
            lock_class=RedisLock,
        )
