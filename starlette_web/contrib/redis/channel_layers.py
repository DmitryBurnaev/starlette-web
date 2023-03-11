from typing import Any, Type

from redis import asyncio as aioredis
from redis.asyncio.client import PubSub
from redis.exceptions import ConnectionError

from starlette_web.common.channels.event import Event
from starlette_web.common.channels.exceptions import ListenerClosed
from starlette_web.common.channels.layers.base import BaseChannelLayer
from starlette_web.common.utils.serializers import BaseSerializer, PickleSerializer


class RedisPubSubChannelLayer(BaseChannelLayer):
    # Cross-process channel layer, uses fire-and-forget scheme
    serializer_class: Type[BaseSerializer] = PickleSerializer
    redis: aioredis.Redis

    def __init__(self, **options):
        super().__init__(**options)
        self.redis = aioredis.Redis(**options)
        self._serializer = self.serializer_class()
        self._pubsub: PubSub = self.redis.pubsub()

    async def connect(self) -> None:
        await self._pubsub.connect()

    async def disconnect(self) -> None:
        await self._pubsub.reset()

    async def subscribe(self, group: str) -> None:
        await self._pubsub.subscribe(group)

    async def unsubscribe(self, group: str) -> None:
        await self._pubsub.unsubscribe(group)

    async def publish(self, group: str, message: Any) -> None:
        message = self._serializer.serialize(
            {
                "group": group,
                "data": message,
            }
        )
        await self.redis.publish(group, message)

    async def next_published(self) -> Event:
        while True:
            try:
                response = await self._pubsub.parse_response(block=True)
            except ConnectionError as exc:
                raise ListenerClosed(details=str(exc)) from exc

            if response is None:
                continue

            message = await self._pubsub.handle_message(response, ignore_subscribe_messages=True)
            if message is None:
                continue

            if hasattr(message, "__getitem__") and "data" in message:
                message = message["data"]
            else:
                continue

            message = self._serializer.deserialize(message)
            return Event(group=message["group"], message=message["data"])
