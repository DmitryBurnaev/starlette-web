from typing import List, Dict, Any, Type, ByteString

from starlette_web.common.http.exceptions import NotSupportedError, UnexpectedError
from starlette_web.common.utils.serializers import (
    BytesSerializer,
    PickleSerializer,
    DeserializeError,
)


class BaseConstanceBackend:
    empty = object()
    serializer_class: Type[BytesSerializer] = PickleSerializer

    def __init__(self):
        self.serializer: BytesSerializer = self.serializer_class()

    def _preprocess_response(self, response: ByteString) -> Any:
        if response is None:
            return self.empty

        if isinstance(response, (memoryview, bytearray)):
            response = bytes(response)

        try:
            return self.serializer.deserialize(response)
        except DeserializeError as exc:
            raise UnexpectedError(details=str(exc)) from exc

    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        raise NotSupportedError(details="Constance backend not initialized.")

    async def get(self, key: str) -> Any:
        raise NotSupportedError(details="Constance backend not initialized.")

    async def set(self, key: str, value: Any) -> None:
        raise NotSupportedError(details="Constance backend not initialized.")
