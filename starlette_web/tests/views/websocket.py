from typing import Dict, Any, Optional

import anyio
from marshmallow import Schema, fields
from marshmallow.validate import OneOf
from starlette.types import Scope, Receive, Send
from starlette.websockets import WebSocket, WebSocketDisconnect

from starlette_web.common.conf import settings
from starlette_web.common.caches import caches
from starlette_web.common.channels.base import Channel
from starlette_web.common.ws.base_endpoint import BaseWSEndpoint
from starlette_web.common.authorization.permissions import IsAuthenticatedPermission
from starlette_web.contrib.auth.backend import JWTAuthenticationBackend
from starlette_web.contrib.redis.channel_layers import RedisPubSubChannelLayer


locmem_cache = caches["locmem"]


class WebsocketRequestSchema(Schema):
    request_type = fields.Str()


class ChatRequestSchema(Schema):
    request_type = fields.Str(
        validate=[
            OneOf(["connect", "publish"]),
        ]
    )
    message = fields.Str(required=False)


class BaseWebsocketTestEndpoint(BaseWSEndpoint):
    request_schema = WebsocketRequestSchema

    async def _background_handler(self, task_id: str, websocket: WebSocket, data: Dict):
        await anyio.sleep(2)
        return data["request_type"]

    async def _register_background_task(self, task_id: str, websocket: WebSocket, data: Dict):
        await locmem_cache.async_set(task_id, 1, timeout=20)

    async def _unregister_background_task(
        self, task_id: str, websocket: WebSocket, task_result: Any
    ):
        await locmem_cache.async_delete(task_id)
        if task_result is not None:
            await locmem_cache.async_set(task_id + "_result", task_result, timeout=20)


class CancellationWebsocketTestEndpoint(BaseWebsocketTestEndpoint):
    async def _background_handler(self, task_id: str, websocket: WebSocket, data: Dict):
        if data["request_type"] == "cancel":
            return

        if data["request_type"] == "fail":
            raise Exception("fail")

        return await super()._background_handler(task_id, websocket, data)

    async def _handle_background_task_exception(
        self, task_id: str, websocket: WebSocket, exc: Exception
    ):
        await locmem_cache.async_set(task_id + "_exception", str(exc), timeout=20)
        raise WebSocketDisconnect(code=1005) from exc


class AuthenticationWebsocketTestEndpoint(BaseWebsocketTestEndpoint):
    auth_backend = JWTAuthenticationBackend
    permission_classes = [IsAuthenticatedPermission]
    EXIT_MAX_DELAY = 5


class FinitePeriodicTaskWebsocketTestEndpoint(BaseWebsocketTestEndpoint):
    EXIT_MAX_DELAY = 5

    async def _background_handler(self, task_id: str, websocket: WebSocket, data: Dict):
        for i in range(4):
            await websocket.send_json({"response": i})
            await anyio.sleep(1)

        return "finished"


class InfinitePeriodicTaskWebsocketTestEndpoint(BaseWebsocketTestEndpoint):
    EXIT_MAX_DELAY = 5

    async def _background_handler(self, task_id: str, websocket: WebSocket, data: Dict):
        prefix = data["request_type"]

        i = 0
        while True:
            await websocket.send_json({"response": prefix + "_" + str(i)})
            await anyio.sleep(1)
            i += 1

    async def _unregister_background_task(
        self, task_id: str, websocket: WebSocket, task_result: Any
    ):
        await locmem_cache.async_delete(task_id)
        # Explicitly set "finished" task_result for tests
        await locmem_cache.async_set(task_id + "_result", "finished", timeout=20)


class ChatWebsocketTestEndpoint(BaseWSEndpoint):
    request_schema = ChatRequestSchema

    def __init__(self, scope: Scope, receive: Receive, send: Send) -> None:
        super().__init__(scope, receive, send)
        self._manager_lock = anyio.Lock()
        self._response_handler_init = False
        self._channels_init = False
        self._channels_wrap: Optional[Channel] = None
        self._channels: Optional[Channel] = None
        self._tasks = set()

    async def _register_background_task(self, task_id: str, websocket: WebSocket, data: Dict):
        async with self._manager_lock:
            if not self._channels_init and data["request_type"] == "connect":
                redis_options = settings.CHANNEL_LAYERS["redispubsub"]["OPTIONS"]
                self._channels_wrap = Channel(RedisPubSubChannelLayer(**redis_options))
                self._channels = await self._channels_wrap.__aenter__()
                self._channels_init = True

            self._tasks.add(task_id)

    async def _background_handler(self, task_id: str, websocket: WebSocket, data: Dict):
        async with self._manager_lock:
            if not self._channels_init:
                return

        if data["request_type"] == "publish":
            await self._channels.publish("chatroom", data["message"])

        elif data["request_type"] == "connect":
            # TODO: examine anyio KeyError due to WeakRef
            # We have to use explicit await here, instead of calling self.task_group.spawn_soon
            # since otherwise this _background_handler will close, call _unregister and close
            # the task_group altogether, since no other tasks are spawned at this moment
            await self._run_dialogue(websocket)

        else:
            raise WebSocketDisconnect(code=1005, reason="Invalid request type")

    async def _unregister_background_task(
        self, task_id: str, websocket: WebSocket, task_result: Any
    ):
        async with self._manager_lock:
            self._tasks.discard(task_id)

            if self._channels_init and not self._tasks:
                await self._channels_wrap.__aexit__(None, None, None)
                self._channels_init = False

    async def _run_dialogue(self, websocket: WebSocket):
        try:
            async with self._manager_lock:
                if self._response_handler_init:
                    return
                self._response_handler_init = True

            async with self._channels.subscribe("chatroom") as subscriber:
                async for event in subscriber:
                    await websocket.send_json(event.message)
        finally:
            async with self._manager_lock:
                self._response_handler_init = False
