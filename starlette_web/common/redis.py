import asyncio
import json
import os
from functools import partial
from typing import Iterable, Any, Union

import redis

from common.utils import get_logger

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

logger = get_logger(__name__)


class RedisClient:
    """The class is used to create a redis connection in a single instance."""

    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            # TODO: can we use https://pypi.org/project/aioredis/ instead?
            cls.redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, max_connections=32)

        return cls.__instance

    def set(self, key: str, value, ttl: int = 120):
        self.redis.set(key, json.dumps(value), ttl)

    def get(self, key: str) -> Union[list[Any], dict[str, Any]]:
        return json.loads(self.redis.get(key) or "null")

    def get_many(self, keys: Iterable[str], pkey: str) -> dict:
        """
        Allows to get several values from redis for 1 request
        :param keys: any iterable object with needed keys
        :param pkey: key in each record for grouping by it
        :return: dict with keys (given from stored records by `pkey`)

        """
        stored_items = map(json.loads, [item for item in self.redis.mget(keys) if item])
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
