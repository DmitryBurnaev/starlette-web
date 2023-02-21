import json
import logging
from typing import ClassVar, Type, Any, Optional, List, Union, Dict, Tuple
import sys

import anyio
from anyio._core._tasks import TaskGroup
from marshmallow import Schema, ValidationError
from starlette.endpoints import WebSocketEndpoint
from starlette.types import Scope, Receive, Send
from starlette.websockets import WebSocket, WebSocketDisconnect

from starlette_web.common.authorization.backends import (
    BaseAuthenticationBackend,
    NoAuthenticationBackend,
)
from starlette_web.common.authorization.base_user import BaseUser, AnonymousUser
from starlette_web.common.authorization.permissions import BasePermission, OperandHolder
from starlette_web.common.http.exceptions import (
    PermissionDeniedError,
    AuthenticationFailedError,
)
from starlette_web.common.ws.requests import WSRequest
from starlette_web.common.utils.crypto import get_random_string


logger = logging.getLogger(__name__)


class BaseWSEndpoint(WebSocketEndpoint):
    auth_backend: ClassVar[Type[BaseAuthenticationBackend]] = NoAuthenticationBackend
    permission_classes: ClassVar[List[Union[Type[BasePermission], OperandHolder]]] = []
    request_schema: ClassVar[Type[Schema]]
    user: BaseUser
    request: WSRequest
    task_group: Optional[TaskGroup]
    EXIT_MAX_DELAY: float = 60

    def __init__(self, scope: Scope, receive: Receive, send: Send) -> None:
        super().__init__(scope, receive, send)
        self.task_group = None

    async def dispatch(self) -> None:
        self.app = self.scope.get("app")  # noqa
        async with anyio.create_task_group() as self.task_group:
            await super().dispatch()

    async def on_connect(self, websocket: WebSocket) -> None:
        self.request = WSRequest.from_websocket(websocket)

        try:
            async with self.app.session_maker() as db_session:
                self.request.db_session = db_session
                self.user = await self._authenticate()
                permitted, reason = await self._check_permissions()
        except Exception as exc:  # pylint: disable=broad-except
            # Any exception must be re-raised to WebSocketDisconnect
            # Otherwise, websocket will hang out,
            # since accept()/close() have not been called
            raise WebSocketDisconnect(code=1006, reason=str(exc)) from exc

        # Explicitly clear db_session,
        # so that user does not use it through lengthy websocket life-state
        self.request.db_session = None

        if permitted:
            await websocket.accept()
        else:
            raise WebSocketDisconnect(code=3000, reason=reason)

    async def on_receive(self, websocket: WebSocket, data: Any) -> None:
        cleaned_data = self._validate(data)
        self.task_group.start_soon(self._background_handler_wrap, websocket, cleaned_data)

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        if self.task_group:
            if sys.exc_info() == (None, None, None):
                self.task_group.cancel_scope.cancel()
                logger.debug("TaskGroup has been explicitly cancelled.")
            else:
                logger.debug("TaskGroup will be implicitly cancelled due to exception.")

        logger.debug("WS connection has been closed.")

    async def _background_handler_wrap(self, websocket: WebSocket, data: Dict):
        task_id = get_random_string(50)
        task_result = None

        try:
            await self._register_background_task(task_id, websocket, data)
            task_result = await self._background_handler(task_id, websocket, data)
        except anyio.get_cancelled_exc_class() as exc:
            logger.debug(f"Background task {task_id} has been cancelled.")
            # As per anyio documentation, CancelError must be always re-raised
            # Note, that it will also cancel all other tasks,
            # due to design of cancellation in anyio 3.x
            # See: https://github.com/agronholm/anyio/pull/496
            raise exc
        except Exception as exc:  # pylint: disable=broad-except
            await self._handle_background_task_exception(task_id, websocket, exc)
        finally:
            # As per anyio documentation, any awaitables,
            # that run within scope of CancelError, must be shielded
            with anyio.fail_after(delay=self.EXIT_MAX_DELAY, shield=True):
                await self._unregister_background_task(task_id, websocket, task_result)

    async def _handle_background_task_exception(
        self, task_id: str, websocket: WebSocket, exc: Exception
    ):
        error_message = "Couldn't finish _background_handler for class %s"
        error_message_message_args = (self.__class__.__name__,)
        logger.exception(error_message, *error_message_message_args)

        # By default, an exception is propagated to the parent TaskGroup,
        # causing an inner CancelScope to cancel all child tasks.
        # If this is not an expected behavior, you may silence this error.
        raise WebSocketDisconnect(code=1005, reason=str(exc)) from exc

    async def _register_background_task(self, task_id: str, websocket: WebSocket, data: Dict):
        # This method is to be redefined in child classes
        pass

    async def _unregister_background_task(
        self, task_id: str, websocket: WebSocket, task_result: Any
    ):
        # This method is to be redefined in child classes
        pass

    async def _background_handler(self, task_id: str, websocket: WebSocket, data: Dict) -> Any:
        raise WebSocketDisconnect(
            code=1005,
            reason="Background handler for Websocket is not implemented",
        )

    def _validate(self, data: str) -> dict:
        try:
            request_data = json.loads(data)
        except json.JSONDecodeError as exc:
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

    async def _authenticate(self) -> BaseUser:
        backend = self.auth_backend(self.request, self.scope)
        try:
            user = await backend.authenticate()
        except AuthenticationFailedError:
            user = AnonymousUser()
        self.scope["user"] = user
        return user

    async def _check_permissions(self) -> Tuple[bool, str]:
        for permission_class in self.permission_classes:
            try:
                has_permission = await permission_class().has_permission(self.request, self.scope)
                if not has_permission:
                    return False, PermissionDeniedError.message
            except PermissionDeniedError as exc:
                return False, str(exc)

        return True, ""
