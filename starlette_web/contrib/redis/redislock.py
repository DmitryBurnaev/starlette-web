import anyio

from aioredis.exceptions import RedisError
from aioredis.lock import Lock as AioredisLock

from starlette_web.common.caches.base import CacheLockError


class RedisLock(AioredisLock):
    EXIT_MAX_DELAY: float = 60

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

                async def close_task():
                    await self.lua_release(
                        keys=[self.name],
                        args=[expected_token],
                        client=self.redis,
                    )

                async with anyio.create_task_group() as nursery:
                    nursery.cancel_scope.deadline = anyio.current_time() + self.EXIT_MAX_DELAY
                    nursery.cancel_scope.shield = True
                    nursery.start_soon(close_task)
        except (RedisError, TimeoutError) as exc:
            raise CacheLockError from exc
