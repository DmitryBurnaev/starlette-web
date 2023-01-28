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
            expected_token = self.local.token
            if expected_token is not None:
                super().__aexit__(*args)
        except RedisError as exc:
            raise CacheLockError from exc
