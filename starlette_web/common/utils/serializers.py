import json
import pickle

from typing import Any


class BaseSerializer:
    def serialize(self, content: Any) -> Any:
        raise NotImplementedError

    def deserialize(self, content: Any) -> Any:
        raise NotImplementedError


class JSONSerializer(BaseSerializer):
    def serialize(self, content: Any) -> Any:
        return json.dumps(content)

    def deserialize(self, content: Any) -> Any:
        return json.loads(content)


class PickleSerializer(BaseSerializer):
    def serialize(self, content: Any) -> Any:
        return pickle.dumps(content)

    def deserialize(self, content: Any) -> Any:
        return pickle.loads(content)
