import json
import pickle

from typing import Any


class BaseSerializer:
    def serialize(self, content: Any) -> Any:
        raise NotImplementedError

    def deserialize(self, content: Any) -> Any:
        raise NotImplementedError

    def __eq__(self, other):
        return self.__class__ == other.__class__


class JSONSerializer(BaseSerializer):
    def serialize(self, content: Any) -> Any:
        return json.dumps(content)

    def deserialize(self, content: Any) -> Any:
        return json.loads(content or "null")


class PickleSerializer(BaseSerializer):
    def serialize(self, content: Any) -> Any:
        return pickle.dumps(content)

    def deserialize(self, content: Any) -> Any:
        return pickle.loads(content)
