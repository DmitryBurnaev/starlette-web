# Copy from https://github.com/vbabiy/djangorestframework-camel-case

import re
from typing import Union
from collections import Container

camelize_re = re.compile(r"[a-z0-9]?_[a-z0-9]")
JSONType = Union[dict, list, str, bool, None]


def _underscore_to_camel(match):
    group = match.group()
    if len(group) == 3:
        return group[0] + group[2].upper()
    else:
        return group[1].upper()


def camelize(data: JSONType, ignore_fields: Container = ()) -> JSONType:
    """
    Recursively swaps snake_case to camelCase in keys of nested dictionaries, leaving values as is.

    >>> from starlette_web.contrib.camel_case import camelize
    >>> camelize({'key_item': 1, 'values_list': [{'object_id': 1, 'object_value': 'new_object_value'}]})  # noqa E501
    [0] {'keyItem': 1, 'valuesList': [{'objectId': 1, 'objectValue': 'new_object_value'}]}
    """
    if isinstance(data, dict):
        new_dict = dict()
        for key, value in data.items():
            if isinstance(key, str) and "_" in key:
                new_key = re.sub(camelize_re, _underscore_to_camel, key)
            else:
                new_key = key
            if key not in ignore_fields and new_key not in ignore_fields:
                new_dict[new_key] = camelize(value, ignore_fields=ignore_fields)
            else:
                new_dict[new_key] = value
        return new_dict

    if _is_iterable(data) and not isinstance(data, str):
        return [camelize(item, ignore_fields=ignore_fields) for item in data]

    return data


def _get_underscoreize_re(no_underscore_before_number=False):
    if no_underscore_before_number:
        pattern = r"([a-z0-9]|[A-Z]?(?=[A-Z](?=[a-z])))([A-Z])"
    else:
        pattern = r"([a-z0-9]|[A-Z]?(?=[A-Z0-9](?=[a-z0-9]|$)))([A-Z]|(?<=[a-z])[0-9](?=[0-9A-Z]|$)|(?<=[A-Z])[0-9](?=[0-9]|$))"  # noqa E501
    return re.compile(pattern)


def _camel_to_underscore(name, no_underscore_before_number=False):
    underscoreize_re = _get_underscoreize_re(
        no_underscore_before_number=no_underscore_before_number
    )
    return underscoreize_re.sub(r"\1_\2", name).lower()


def underscoreize(
    data: JSONType,
    ignore_fields: Container = (),
    no_underscore_before_number: bool = False,
) -> JSONType:
    """
    Recursively swaps camelCase to snake_case in keys of nested dictionaries, leaving values as is.

    >>> from starlette_web.contrib.camel_case import underscoreize
    >>> underscoreize({'keyItem': 1, 'valuesList': [{'objectId': 1, 'objectValue': 'newObjectValue'}]})  # noqa E501
    [0] {'key_item': 1, 'values_list': [{'object_id': 1, 'object_value': 'newObjectValue'}]}
    """
    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            if isinstance(key, str):
                new_key = _camel_to_underscore(
                    key,
                    no_underscore_before_number=no_underscore_before_number,
                )
            else:
                new_key = key

            if isinstance(value, str):
                new_dict[new_key] = value
            elif (key not in ignore_fields) and (new_key not in ignore_fields):
                new_dict[new_key] = underscoreize(
                    value,
                    ignore_fields=ignore_fields,
                    no_underscore_before_number=no_underscore_before_number,
                )
            else:
                new_dict[new_key] = value

        return new_dict

    if _is_iterable(data) and not isinstance(data, str):
        return [
            underscoreize(
                item,
                ignore_fields=ignore_fields,
                no_underscore_before_number=no_underscore_before_number,
            )
            for item in data
        ]

    return data


def _is_iterable(obj):
    try:
        _ = iter(obj)
        return True
    except TypeError:
        return False
