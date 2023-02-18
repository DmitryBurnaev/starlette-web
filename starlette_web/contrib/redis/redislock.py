import anyio

from aioredis.exceptions import RedisError
from aioredis.lock import Lock as AioredisLock

from starlette_web.common.caches.base import CacheLockError


class RedisLock(AioredisLock):
    EXIT_MAX_DELAY = 10

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
                with anyio.move_on_after(self.EXIT_MAX_DELAY, shield=True):
                    await self.lua_release(
                        keys=[self.name],
                        args=[expected_token],
                        client=self.redis,
                    )
        except RedisError as exc:
            raise CacheLockError from exc
