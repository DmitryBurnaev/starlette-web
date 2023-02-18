import asyncio
import json
import logging
from json import JSONDecodeError
from typing import ClassVar, Type, Any, Optional
import sys

import anyio
from anyio._core._tasks import TaskGroup, CancelScope
from marshmallow import Schema
from sqlalchemy.exc import InvalidRequestError
from starlette.endpoints import WebSocketEndpoint
from starlette.types import Scope, Receive, Send
from starlette.websockets import WebSocket

from starlette_web.common.authorization.base_user import BaseUserMixin
from starlette_web.contrib.auth.backend import JWTAuthenticationBackend
from starlette_web.common.ws.requests import WSRequest
from starlette_web.common.ws.schemas import WSRequestAuthSchema
from starlette_web.common.authorization.backends import BaseAuthenticationBackend


logger = logging.getLogger(__name__)


class BaseWSEndpoint(WebSocketEndpoint):
    auth_backend: ClassVar[Type[BaseAuthenticationBackend]] = JWTAuthenticationBackend
    request_schema: ClassVar[Type[Schema]] = WSRequestAuthSchema
    user: BaseUserMixin
    request: WSRequest
    background_task: asyncio.Task
    task_group: Optional[TaskGroup]
    cancel_scope: Optional[CancelScope]

    def __init__(self, scope: Scope, receive: Receive, send: Send) -> None:
        super().__init__(scope, receive, send)
        self.task_group = None
        self.cancel_scope = None

    async def dispatch(self) -> None:
        self.app = self.scope.get("app")  # noqa
        async with anyio.create_task_group() as self.task_group:
            with anyio.CancelScope() as self.cancel_scope:
                await super().dispatch()

    async def on_connect(self, websocket: WebSocket) -> None:
        await websocket.accept()

    async def on_receive(self, websocket: WebSocket, data: Any) -> None:
        """
        On receive 1st message from WS client,
        we have to get header's like data with JWT token provided
        (like {"headers": {"authorization": "Bearer <JWT_TOKEN>"}, "data": {<some-data>}})
        It allows to authorize current user for each WS connection.
        """

        cleaned_data = self._validate(data)
        self.request = WSRequest(headers=cleaned_data["headers"], data=cleaned_data)
        self.user = await self._auth()
        self.task_group.start_soon(self._background_handler_wrap, websocket)

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        if self.task_group and self.cancel_scope:
            self.cancel_scope.__exit__(*sys.exc_info())
            logger.info("Background task '_background_handler' was canceled")

        logger.info("WS connection was closed")

    async def _background_handler_wrap(self, websocket: WebSocket):
        try:
            await self._background_handler(websocket)
        except anyio.get_cancelled_exc_class():
            # Task cancellation should not be logged as an error.
            pass
        except Exception:  # pylint: disable=broad-except
            error_message = "Couldn't finish _background_handler for class %s"
            error_message_message_args = (self.__class__.__name__,)
            logger.exception(error_message, *error_message_message_args)

    async def _background_handler(self, websocket: WebSocket):
        raise NotImplementedError

    def _validate(self, data: str) -> dict:
        try:
            request_data = json.loads(data)
        except JSONDecodeError as exc:
            raise InvalidRequestError(f"Couldn't parse WS request data: {exc}") from exc

        return self.request_schema().load(request_data)

    async def _auth(self) -> BaseUserMixin:
        async with self.app.session_maker() as db_session:
            backend = self.auth_backend(self.request, db_session)
            user, _ = await backend.authenticate()
            self.scope["user"] = user

        return user
