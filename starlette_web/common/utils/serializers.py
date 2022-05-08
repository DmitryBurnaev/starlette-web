import json
import pickle

from typing import Any


# TODO: generic SerializeError, DeserializeError
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
        return self.encoder_class().encode(content)

    def deserialize(self, content: Any) -> Any:
        return self.decoder_class().decode(content or "null")


class PickleSerializer(BaseSerializer):
    # TODO: maybe add option to use dill ?
    def serialize(self, content: Any) -> Any:
        return pickle.dumps(content)

    def deserialize(self, content: Any) -> Any:
        return pickle.loads(content)
