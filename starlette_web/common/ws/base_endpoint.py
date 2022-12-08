import asyncio
import json
import logging
from json import JSONDecodeError
from typing import ClassVar, Type, Any

from marshmallow import Schema
from sqlalchemy.exc import InvalidRequestError
from starlette.endpoints import WebSocketEndpoint
from starlette.websockets import WebSocket

from common.utils.async_utils import create_task
from contrib.auth.models import User
from starlette_web.contrib.auth.backend import JWTAuthenticationBackend
from starlette_web.common.ws.requests import WSRequest
from starlette_web.common.ws.schemas import WSRequestAuthSchema
from starlette_web.common.authorization.backends import BaseAuthenticationBackend


logger = logging.getLogger(__name__)


class BaseWSEndpoint(WebSocketEndpoint):
    auth_backend: ClassVar[Type[BaseAuthenticationBackend]] = JWTAuthenticationBackend
    request_schema: ClassVar[Type[Schema]] = WSRequestAuthSchema
    user: User
    request: WSRequest
    background_task: asyncio.Task

    async def dispatch(self) -> None:
        self.app = self.scope.get("app")  # noqa
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
        self.background_task = create_task(
            self._background_handler(websocket),
            logger=logger,
            error_message="Couldn't finish _background_handler for class %s",
            error_message_message_args=(self.__class__.__name__,),
        )

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        if self.background_task:
            self.background_task.cancel()
            logger.info("Background task '_background_handler' was canceled")

        logger.info("WS connection was closed")

    async def _background_handler(self, websocket: WebSocket):
        raise NotImplementedError

    def _validate(self, data: str) -> dict:
        try:
            request_data = json.loads(data)
        except JSONDecodeError as exc:
            raise InvalidRequestError(f"Couldn't parse WS request data: {exc}") from exc

        return self.request_schema().load(request_data)

    async def _auth(self) -> User:
        async with self.app.session_maker() as db_session:
            backend = self.auth_backend(self.request, db_session)
            user, _ = await backend.authenticate()
            self.scope["user"] = user

        return user
