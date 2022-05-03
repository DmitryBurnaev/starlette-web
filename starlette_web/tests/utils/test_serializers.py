from starlette_web.common.utils.serializers import JSONSerializer, PickleSerializer


def test_json_serializer():
    serializer = JSONSerializer()

    obj = {
        'list_1': [{'bool_key': True, 'int_key': 1}],
        'obj_key': {'null_key': None, 'str_key': 'string'},
    }

    encoded = serializer.serialize(obj)
    assert type(encoded) == str

    decoded = serializer.deserialize(encoded)
    assert obj == decoded

    obj = None
    assert serializer.deserialize(serializer.serialize(obj)) is None


def test_pickle_serializer():
    serializer = PickleSerializer()

    obj = {
        'list_1': [{'bool_key': True, 'int_key': 1}],
        'obj_key': {'null_key': None, 'str_key': 'string'},
        'class_key': JSONSerializer,
        'object_key': JSONSerializer(),
        'method_key': JSONSerializer.serialize,
    }

    encoded = serializer.serialize(obj)
    assert type(encoded) == bytes

    decoded = serializer.deserialize(encoded)
    assert obj == decoded
