import json
import pickle
from typing import Any

from starlette_web.common.http.exceptions import BaseApplicationError


class SerializerError(BaseApplicationError):
    pass


class SerializeError(SerializerError):
    pass


class DeserializeError(SerializerError):
    pass


class BaseSerializer:
    def serialize(self, content: Any) -> Any:
        raise NotImplementedError

    def deserialize(self, content: Any) -> Any:
        raise NotImplementedError

    def __eq__(self, other):
        return self.__class__ == other.__class__


class JSONSerializer(BaseSerializer):
    encoder_class = json.JSONEncoder
    decoder_class = json.JSONDecoder

    def serialize(self, content: Any) -> Any:
        try:
            return self.encoder_class().encode(content)
        except ValueError as exc:
            raise SerializeError from exc

    def deserialize(self, content: Any) -> Any:
        try:
            return self.decoder_class().decode(content or "null")
        except ValueError as exc:
            raise DeserializeError from exc


class PickleSerializer(BaseSerializer):
    # TODO: maybe add option to use dill ?
    def serialize(self, content: Any) -> Any:
        try:
            return pickle.dumps(content)
        except pickle.PicklingError as exc:
            raise SerializeError from exc

    def deserialize(self, content: Any) -> Any:
        if content is None:
            return None

        try:
            return pickle.loads(content)
        except pickle.UnpicklingError as exc:
            raise DeserializeError from exc
