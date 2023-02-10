import asyncio

from aioredis.exceptions import RedisError
from aioredis.lock import Lock as AioredisLock

from starlette_web.common.caches.base import CacheLockError


class RedisLock(AioredisLock):
    async def __aenter__(self):
        try:
            return await super().__aenter__()
        except RedisError as exc:
            raise CacheLockError from exc

    async def __aexit__(self, *args):
        try:
            # Do not raise exception, if lock has been released
            # (might have been released due to timeout)
            expected_token = self.local.token
            if expected_token is not None:
                self.local.token = None
                coroutine = self.lua_release(
                    keys=[self.name],
                    args=[expected_token],
                    client=self.redis,
                )
                await asyncio.shield(coroutine)
        except RedisError as exc:
            raise CacheLockError from exc
