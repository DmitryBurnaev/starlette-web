from collections import OrderedDict

from starlette_web.contrib.camel_case import camelize, underscoreize


def test_contrib_camelcase_camelize():
    obj = {
        'key_item': 1,
        'values_list': [
            {
                'object_id': 1,
                'object_value': 'new_object_value',
            },
            {
                'object_id': 1,
                'object_value': 'new_object_value',
            },
        ],
    }

    result = OrderedDict([
        ('keyItem', 1),
        ('valuesList', [
            OrderedDict([('objectId', 1), ('objectValue', 'new_object_value')]),
            OrderedDict([('objectId', 1), ('objectValue', 'new_object_value')]),
        ]),
    ])

    assert camelize(obj) == result


def test_contrib_camelcase_underscoreize():
    obj = {
        'keyItem': 1,
        'valuesList': [
            {
                'objectId': 1,
                'objectValue': 'newObjectValue',
            },
            {
                'objectId': 2,
                'objectValue': 'newObjectValue',
            },
        ],
    }

    result = {
        'key_item': 1,
        'values_list': [
            {
                'object_id': 1,
                'object_value': 'newObjectValue',
            },
            {
                'object_id': 2,
                'object_value': 'newObjectValue',
            },
        ],
    }

    assert underscoreize(obj) == result


def test_strings_are_left_as_is():
    assert camelize('a_b') == 'a_b'
    assert underscoreize('aB') == 'aB'
