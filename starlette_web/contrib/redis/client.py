import asyncio
from functools import partial
from typing import Iterable, Any, Union, List, Dict, Type

import redis

from starlette_web.common.utils import get_logger, Singleton
from starlette_web.common.utils.serializers import BaseSerializer, JSONSerializer
from starlette_web.core import settings

logger = get_logger(__name__)


class RedisClient(metaclass=Singleton):
    # TODO: inherit from BaseCache
    # TODO: can we use https://pypi.org/project/aioredis/ instead?
    """The class is used to create a redis connection in a single instance."""

    __instance = None
    serializer_class: Type[BaseSerializer] = JSONSerializer
    redis = redis.Redis

    def __init__(self):
        self.serializer = self.serializer_class()
        self.redis = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, max_connections=32)

    def set(self, key: str, value, ttl: int = 120):
        self.redis.set(key, self.serializer.serialize(value), ttl)

    def get(self, key: str) -> Union[List[Any], Dict[str, Any]]:
        return self.serializer.deserialize(self.redis.get(key))

    def get_many(self, keys: Iterable[str], pkey: str) -> dict:
        """
        Allows to get several values from redis for 1 request
        :param keys: any iterable object with needed keys
        :param pkey: key in each record for grouping by it
        :return: dict with keys (given from stored records by `pkey`)

        """
        stored_items = map(self.serializer.deserialize, [item for item in self.redis.mget(keys) if item])
        try:
            result = {stored_item[pkey]: stored_item for stored_item in stored_items}
        except (TypeError, KeyError) as error:
            logger.debug("Try to extract redis data: %s", list(stored_items))
            logger.exception("Couldn't extract event data from redis: %s", error)
            result = {}

        return result

    async def async_get_many(self, keys: Iterable[str], pkey: str) -> dict:
        loop = asyncio.get_running_loop()
        get_many_handler = partial(self.get_many, keys, pkey=pkey)
        return await loop.run_in_executor(None, get_many_handler)

    @staticmethod
    def get_key_by_filename(filename) -> str:
        return filename.partition(".")[0]
