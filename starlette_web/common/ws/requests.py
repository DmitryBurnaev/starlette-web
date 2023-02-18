from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocket


class WSRequest(WebSocket):
    db_session: Optional[AsyncSession] = None

    @classmethod
    def from_websocket(cls, websocket):
        obj = cls(
            scope=websocket.scope,
            receive=websocket.receive,
            send=websocket.send,
        )
        obj.client_state = websocket.client_state
        obj.application_state = websocket.application_state
        return obj
