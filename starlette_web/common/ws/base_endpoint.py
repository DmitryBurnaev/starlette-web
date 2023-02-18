import asyncio
import json
import logging
from json import JSONDecodeError
from typing import ClassVar, Type, Any, Optional, List, Union, Dict, Tuple
import sys

import anyio
from anyio._core._tasks import TaskGroup
from marshmallow import Schema, ValidationError
from starlette.endpoints import WebSocketEndpoint
from starlette.types import Scope, Receive, Send
from starlette.websockets import WebSocket, WebSocketDisconnect

from starlette_web.common.authorization.backends import (
    BaseAuthenticationBackend, NoAuthenticationBackend,
)
from starlette_web.common.authorization.base_user import BaseUserMixin
from starlette_web.common.authorization.permissions import BasePermission, OperandHolder
from starlette_web.common.http.exceptions import PermissionDeniedError
from starlette_web.common.ws.requests import WSRequest
from starlette_web.common.utils.crypto import get_random_string


logger = logging.getLogger(__name__)


class BaseWSEndpoint(WebSocketEndpoint):
    auth_backend: ClassVar[Type[BaseAuthenticationBackend]] = NoAuthenticationBackend
    permission_classes: ClassVar[List[Union[Type[BasePermission], OperandHolder]]] = []
    request_schema: ClassVar[Type[Schema]]
    user: BaseUserMixin
    request: WSRequest
    background_task: asyncio.Task
    task_group: Optional[TaskGroup]

    def __init__(self, scope: Scope, receive: Receive, send: Send) -> None:
        super().__init__(scope, receive, send)
        self.task_group = None

    async def dispatch(self) -> None:
        self.app = self.scope.get("app")  # noqa
        async with anyio.create_task_group() as self.task_group:
            await super().dispatch()

    async def on_connect(self, websocket: WebSocket) -> None:
        self.request = WSRequest.from_websocket(websocket)
        async with self.app.session_maker() as db_session:
            self.request.db_session = db_session
            self.user = await self._authenticate()
            permitted, reason = await self._check_permissions()

        # Explicitly clear db_session,
        # so that user does not use through lengthy websocket life-state
        self.request.db_session = None

        if permitted:
            await websocket.accept()
        else:
            await websocket.close(code=3000, reason=reason)

    async def on_receive(self, websocket: WebSocket, data: Any) -> None:
        """
        On receive 1st message from WS client,
        we have to get header's like data with JWT token provided
        (like {"headers": {"authorization": "Bearer <JWT_TOKEN>"}, "data": {<some-data>}})
        It allows to authorize current user for each WS connection.
        """

        cleaned_data = self._validate(data)
        self.task_group.start_soon(self._background_handler_wrap, websocket, cleaned_data)

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        if self.task_group:
            self.task_group.cancel_scope.cancel()
            await self.task_group.__aexit__(*sys.exc_info())

        logger.info("WS connection was closed")

    async def _background_handler_wrap(self, websocket: WebSocket, data: Dict):
        task_id = get_random_string(50)

        try:
            await self._register_background_task(task_id, websocket, data)
            await self._background_handler(websocket, data)
        except anyio.get_cancelled_exc_class():
            # Task cancellation should not be logged as an error.
            pass
        except Exception:  # pylint: disable=broad-except
            error_message = "Couldn't finish _background_handler for class %s"
            error_message_message_args = (self.__class__.__name__,)
            logger.exception(error_message, *error_message_message_args)
        finally:
            await self._unregister_background_task(task_id, websocket)

    async def _register_background_task(self, task_id: str, websocket: WebSocket, data: Dict):
        # This method is to be redefined in child classes
        pass

    async def _unregister_background_task(self, task_id: str, websocket: WebSocket):
        # This method is to be redefined in child classes
        pass

    async def _background_handler(self, websocket: WebSocket, data: Dict):
        raise WebSocketDisconnect(
            code=1005,
            reason="Background handler for Websocket is not implemented",
        )

    def _validate(self, data: str) -> dict:
        try:
            request_data = json.loads(data)
        except JSONDecodeError as exc:
            raise WebSocketDisconnect(
                code=1003,
                reason=f"Couldn't parse WS request data: {exc}",
            ) from exc

        try:
            return self.request_schema().load(request_data)
        except ValidationError as exc:
            # TODO: check that details is str / flatten
            raise WebSocketDisconnect(
                code=1007,
                reason=exc.data,
            ) from exc

    async def _authenticate(self) -> BaseUserMixin:
        backend = self.auth_backend(self.request, self.scope)
        user, _ = await backend.authenticate()
        self.scope["user"] = user
        return user

    async def _check_permissions(self) -> Tuple[bool, str]:
        for permission_class in self.permission_classes:
            try:
                has_permission = await permission_class().has_permission(self.request, self.scope)
                if not has_permission:
                    return False, PermissionDeniedError.message

                return True, ""
            # Exception may be raised inside permission_class, to pass additional details
            except PermissionDeniedError as exc:
                return False, str(exc)
            except Exception as exc:
                return False, str(exc)
