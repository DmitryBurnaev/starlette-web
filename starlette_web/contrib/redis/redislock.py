from aioredis.exceptions import RedisError
from aioredis.lock import Lock as AioredisLock

from starlette_web.common.caches.base import CacheLockError


class RedisLock(AioredisLock):
    async def __aenter__(self):
        try:
            return super().__aenter__()
        except RedisError as exc:
            raise CacheLockError from exc

    def __aexit__(self, *args):
        try:
            super().__aexit__(*args)
        except RedisError as exc:
            raise CacheLockError from exc
