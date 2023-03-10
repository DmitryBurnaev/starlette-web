import anyio
from anyio.streams.memory import (
    MemoryObjectReceiveStream,
    MemoryObjectSendStream,
)
from typing import Set, Any, Optional

from starlette_web.common.channels.event import Event
from starlette_web.common.channels.layers.base import BaseChannelLayer


class InMemoryChannelLayer(BaseChannelLayer):
    def __init__(self, **options):
        super().__init__(**options)
        self._subscribed: Set = set()
        self._receive_stream: Optional[MemoryObjectReceiveStream] = None
        self._send_stream: Optional[MemoryObjectSendStream] = None

    async def connect(self) -> None:
        self._send_stream, self._receive_stream = anyio.create_memory_object_stream()

    async def disconnect(self) -> None:
        self._subscribed.clear()
        self._send_stream = None
        self._receive_stream = None

    async def subscribe(self, group: str) -> None:
        self._subscribed.add(group)

    async def unsubscribe(self, group: str) -> None:
        self._subscribed.remove(group)

    async def publish(self, group: str, message: Any) -> None:
        event = Event(group=group, message=message)
        await self._send_stream.send(event)

    async def next_published(self) -> Event:
        assert self._receive_stream
        while True:
            event = await self._receive_stream.receive()
            if event.group in self._subscribed:
                return event
