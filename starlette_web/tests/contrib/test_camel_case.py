from starlette_web.contrib.camel_case import camelize, underscoreize


def test_contrib_camelcase_camelize():
    obj = {
        "key_item": 1,
        "values_list": [
            {
                "object_id": 1,
                "object_value": "new_object_value",
            },
            {
                "object_id": 1,
                "object_value": "new_object_value",
            },
        ],
    }

    result = {
        "keyItem": 1,
        "valuesList": [
            {"objectId": 1, "objectValue": "new_object_value"},
            {"objectId": 1, "objectValue": "new_object_value"},
        ],
    }

    assert camelize(obj) == result

    obj = [
        None,
        {"item_key": "item_value"},
        "StringValue",
        False,
    ]

    result = [None, {"itemKey": "item_value"}, "StringValue", False]

    assert camelize(obj) == result


def test_contrib_camelcase_underscoreize():
    obj = {
        "keyItem": 1,
        "valuesList": [
            {
                "objectId": 1,
                "objectValue": "newObjectValue",
            },
            {
                "objectId": 2,
                "objectValue": "newObjectValue",
            },
        ],
    }

    result = {
        "key_item": 1,
        "values_list": [
            {
                "object_id": 1,
                "object_value": "newObjectValue",
            },
            {
                "object_id": 2,
                "object_value": "newObjectValue",
            },
        ],
    }

    assert underscoreize(obj) == result

    obj = [
        None,
        {"itemKey": "itemValue"},
        "StringValue",
        False,
    ]

    result = [None, {"item_key": "itemValue"}, "StringValue", False]

    assert underscoreize(obj) == result


def test_strings_are_left_as_is():
    assert camelize("a_b") == "a_b"
    assert underscoreize("aB") == "aB"
