import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator, AsyncIterator, Optional, Any, Dict, Set

import anyio
from anyio._core._tasks import TaskGroup
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream

from starlette_web.common.channels.layers.base import BaseChannelLayer
from starlette_web.common.channels.event import Event
from starlette_web.common.channels.exceptions import Unsubscribed, ListenerClosed


_empty = object()


class Channel:
    EXIT_MAX_DELAY = 60

    def __init__(self, channel_layer: BaseChannelLayer):
        self._task_group: Optional[TaskGroup] = None
        self._channel_layer = channel_layer
        self._subscribers: Dict[str, Set[MemoryObjectSendStream]] = dict()
        self._manager_lock = anyio.Lock()
        self._task_group_handler = None

    async def __aenter__(self) -> "Channel":
        self._task_group_handler = anyio.create_task_group()
        self._task_group = await self._task_group_handler.__aenter__()
        await self.connect()
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any):
        with anyio.fail_after(self.EXIT_MAX_DELAY, shield=True):
            await self.disconnect()
            self._subscribers.clear()

        self._task_group.cancel_scope.cancel()
        await self._task_group_handler.__aexit__(*args)

    async def shutdown(self):
        # Helper for starlette.router.shutdown, which does not accept arguments
        await self.__aexit__(*sys.exc_info())

    async def connect(self) -> None:
        await self._channel_layer.connect()
        self._task_group.start_soon(self._listener)

    async def disconnect(self) -> None:
        await self._channel_layer.disconnect()

    async def _listener(self) -> None:
        while True:
            try:
                event = await self._channel_layer.next_published()
            except ListenerClosed:
                break

            async with self._manager_lock:
                subscribers_list = list(self._subscribers.get(event.group, []))

            async with anyio.create_task_group() as nursery:
                for send_stream in subscribers_list:
                    nursery.start_soon(send_stream.send, event)

    async def publish(self, group: str, message: Any) -> None:
        await self._channel_layer.publish(group, message)

    @asynccontextmanager
    async def subscribe(self, group: str) -> AsyncIterator["Subscriber"]:
        send_stream, receive_stream = anyio.create_memory_object_stream()

        try:
            async with self._manager_lock:
                if not self._subscribers.get(group):
                    await self._channel_layer.subscribe(group)
                    self._subscribers[group] = {
                        send_stream,
                    }
                else:
                    self._subscribers[group].add(send_stream)

            yield Subscriber(receive_stream)

        finally:
            try:
                with anyio.fail_after(self.EXIT_MAX_DELAY, shield=True):
                    async with self._manager_lock:
                        self._subscribers[group].remove(send_stream)
                        if not self._subscribers.get(group):
                            del self._subscribers[group]

                            await self._channel_layer.unsubscribe(group)

            except anyio.get_cancelled_exc_class():
                receive_stream.close()
                send_stream.close()

            finally:
                await send_stream.send(_empty)


class Subscriber:
    def __init__(self, receive_stream: MemoryObjectReceiveStream) -> None:
        self._receive_stream = receive_stream

    async def __aiter__(self) -> Optional[AsyncGenerator]:
        try:
            while True:
                yield await self.receive()
        except Unsubscribed:
            pass

    async def receive(self) -> Event:
        item = await self._receive_stream.receive()
        if item is _empty:
            raise Unsubscribed()

        return item
