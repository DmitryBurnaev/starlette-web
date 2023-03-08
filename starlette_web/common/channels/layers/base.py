from typing import Any

from starlette_web.common.channels.event import Event
from starlette_web.common.http.exceptions import NotSupportedError


class BaseChannelLayer:
    def __init__(self, **options) -> None:
        pass

    async def connect(self) -> None:
        raise NotSupportedError()

    async def disconnect(self) -> None:
        raise NotSupportedError()

    async def subscribe(self, group: str) -> None:
        raise NotSupportedError()

    async def unsubscribe(self, group: str) -> None:
        raise NotSupportedError()

    async def publish(self, group: str, message: Any) -> None:
        raise NotSupportedError()

    async def next_published(self) -> Event:
        raise NotSupportedError()
