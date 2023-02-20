from typing import Dict, Any

import anyio
from marshmallow import Schema, fields
from starlette.websockets import WebSocket, WebSocketDisconnect

from starlette_web.common.caches import caches
from starlette_web.common.ws.base_endpoint import BaseWSEndpoint
from starlette_web.common.authorization.permissions import IsAuthenticatedPermission
from starlette_web.contrib.auth.backend import JWTAuthenticationBackend


locmem_cache = caches["locmem"]


class WebsocketRequestSchema(Schema):
    request_type = fields.Str()


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
