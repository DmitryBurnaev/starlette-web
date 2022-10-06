import pickle
from typing import List, Dict, Any, Type

from starlette_web.common.app import AppClass
from starlette_web.common.http.exceptions import NotSupportedError, UnexpectedError
from starlette_web.common.utils.serializers import BaseSerializer, PickleSerializer


class BaseConstanceBackend:
    app: AppClass
    empty = object()
    serializer_class: Type[BaseSerializer] = PickleSerializer

    def __init__(self):
        self.serializer: BaseSerializer = self.serializer_class()

    def _preprocess_response(self, response):
        if response is None:
            return self.empty

        if type(response) != bytes:
            raise NotSupportedError

        try:
            return self.serializer.deserialize(response)
        except pickle.PickleError as exc:
            raise UnexpectedError(details=str(exc))

    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        raise NotImplementedError

    async def get(self, key: str) -> Any:
        raise NotImplementedError

    async def set(self, key: str, value: Any) -> None:
        raise NotImplementedError
