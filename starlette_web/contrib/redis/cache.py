from typing import Sequence, Any, List, Dict, Type, Optional, AsyncContextManager, Union

from redis import asyncio as aioredis

from starlette_web.common.caches.base import BaseCache, CacheError
from starlette_web.common.http.exceptions import UnexpectedError
from starlette_web.common.utils.serializers import BytesSerializer, PickleSerializer
from starlette_web.contrib.redis.redislock import RedisLock


def reraise_exception(func):
    async def wrapped(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except aioredis.RedisError as exc:
            raise CacheError from exc
        except Exception as exc:
            raise UnexpectedError from exc

    return wrapped


class RedisCache(BaseCache):
    redis: aioredis.Redis
    serializer_class: Type[BytesSerializer] = PickleSerializer
    lock_class = RedisLock

    def __init__(self, options: Dict[str, Any]):
        super().__init__(options)
        self.redis = aioredis.Redis(**options)

    @reraise_exception
    async def async_get(self, key: str) -> Any:
        value = await self.redis.get(key)
        return self.serializer.deserialize(value)

    @reraise_exception
    async def async_set(self, key: str, value, timeout: Optional[float] = 120):
        await self.redis.set(
            key,
            self.serializer.serialize(value),
            px=int(timeout * 1000) if timeout is not None else None,
        )

    @reraise_exception
    async def async_delete(self, key: str) -> None:
        await self.redis.delete(key)

    @reraise_exception
    async def async_keys(self, pattern: str) -> List[str]:
        # Using KEYS is not recommended in production with high-load,
        # since it's a redis-blocking operation
        # If you have millions of keys, consider using redis.scan_iter instead
        return [self._force_str(key) for key in (await self.redis.keys(pattern))]

    @reraise_exception
    async def async_get_many(self, keys: Sequence[str]) -> Dict[str, Any]:
        result = dict()
        key_idx = 0

        # redis.mget returns a simple list
        for value in await self.redis.mget(keys):
            result[keys[key_idx]] = self.serializer.deserialize(value)
            key_idx += 1

        return result

    @reraise_exception
    async def async_has_key(self, key: str) -> bool:
        return bool(await self.redis.exists(key))

    @reraise_exception
    async def async_set_many(self, data: Dict[str, Any], timeout: Optional[float] = 120) -> None:
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
                        "PX",
                        int(timeout * 1000),
                    )
                await pipeline.execute(raise_on_error=True)

    @reraise_exception
    async def async_delete_many(self, keys: Sequence[str]) -> None:
        await self.redis.delete(*keys)

    @reraise_exception
    async def async_clear(self) -> None:
        await self.redis.flushdb()

    def lock(
        self,
        name: str,
        timeout: Optional[float] = 20.0,
        blocking_timeout: Optional[float] = None,
        **kwargs,
    ) -> AsyncContextManager:
        # Warning: may hang, if sleep (default 0.1) is less than timeout/blocking_timeout
        # May be connected to https://github.com/redis/redis-py/issues/2579
        kwargs.pop("sleep", 0)

        return self.redis.lock(
            name,
            timeout=timeout,
            blocking_timeout=blocking_timeout,
            lock_class=self.lock_class,
            sleep=0,
            **kwargs,
        )

    @staticmethod
    def _force_str(value: Union[bytes, str]) -> str:
        try:
            return value.decode()
        except (UnicodeDecodeError, AttributeError):
            return str(value)
