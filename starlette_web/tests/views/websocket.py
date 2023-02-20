from typing import Dict, Any

import anyio
from marshmallow import Schema, fields
from starlette.websockets import WebSocket

from starlette_web.common.caches import caches
from starlette_web.common.ws.base_endpoint import BaseWSEndpoint
from starlette_web.common.authorization.permissions import IsAuthenticatedPermission
from starlette_web.contrib.auth.backend import JWTAuthenticationBackend


locmem_cache = caches["locmem"]


class WebsocketRequestSchema(Schema):
    request_type = fields.Str()


class BaseWebsocketTestEndpoint(BaseWSEndpoint):
    request_schema = WebsocketRequestSchema

    async def _background_handler(self, websocket: WebSocket, data: Dict):
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
    async def _background_handler(self, websocket: WebSocket, data: Dict):
        if data["request_type"] == "cancel":
            return

        if data["request_type"] == "fail":
            raise Exception("fail")

        return await super()._background_handler(websocket, data)

    async def _handle_background_task_exception(
        self, task_id: str, websocket: WebSocket, exc: Exception
    ):
        await locmem_cache.async_set(task_id + "_exception", str(exc), timeout=20)
        raise exc


class AuthenticationWebsocketTestEndpoint(BaseWebsocketTestEndpoint):
    auth_backend = JWTAuthenticationBackend
    permission_classes = [IsAuthenticatedPermission]
    EXIT_MAX_DELAY = 5
