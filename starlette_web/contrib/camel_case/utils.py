# Copy from https://github.com/vbabiy/djangorestframework-camel-case

import re
from collections import OrderedDict

camelize_re = re.compile(r"[a-z0-9]?_[a-z0-9]")


def _underscore_to_camel(match):
    group = match.group()
    if len(group) == 3:
        return group[0] + group[2].upper()
    else:
        return group[1].upper()


def camelize(data, **options):
    """
    Recursively swaps snake_case to camelCase in keys of nested dictionaries, leaving values as is.

    >>> from starlette_web.contrib.camel_case import underscoreize
    >>> camelize({'key_item': 1, 'values_list': [{'object_id': 1, 'object_value': 'new_object_value'}]})
    [0] OrderedDict([('keyItem', 1), ('valuesList', [OrderedDict([('objectId', 1), ('objectValue', 'new_object_value')])])])  # noqa E501
    """
    ignore_fields = options.get("ignore_fields") or ()

    if isinstance(data, dict):
        new_dict = OrderedDict()
        for key, value in data.items():
            if isinstance(key, str) and "_" in key:
                new_key = re.sub(camelize_re, _underscore_to_camel, key)
            else:
                new_key = key
            if key not in ignore_fields and new_key not in ignore_fields:
                new_dict[new_key] = camelize(value, **options)
            else:
                new_dict[new_key] = value
        return new_dict

    if _is_iterable(data) and not isinstance(data, str):
        return [camelize(item, **options) for item in data]

    return data


def _get_underscoreize_re(options):
    if options.get("no_underscore_before_number"):
        pattern = r"([a-z0-9]|[A-Z]?(?=[A-Z](?=[a-z])))([A-Z])"
    else:
        pattern = r"([a-z0-9]|[A-Z]?(?=[A-Z0-9](?=[a-z0-9]|$)))([A-Z]|(?<=[a-z])[0-9](?=[0-9A-Z]|$)|(?<=[A-Z])[0-9](?=[0-9]|$))"  # noqa E501
    return re.compile(pattern)


def _camel_to_underscore(name, **options):
    underscoreize_re = _get_underscoreize_re(options)
    return underscoreize_re.sub(r"\1_\2", name).lower()


def underscoreize(data, **options):
    """
    Recursively swaps camelCase to snake_case in keys of nested dictionaries, leaving values as is.

    >>> from starlette_web.contrib.camel_case import underscoreize
    >>> underscoreize({'keyItem': 1, 'valuesList': [{'objectId': 1, 'objectValue': 'newObjectValue'}]})  # noqa E501
    [0] {'key_item': 1, 'values_list': [{'object_id': 1, 'object_value': 'newObjectValue'}]}
    """
    ignore_fields = options.get("ignore_fields") or ()

    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            if isinstance(key, str):
                new_key = _camel_to_underscore(key, **options)
            else:
                new_key = key

            if isinstance(value, str):
                new_dict[new_key] = value
            elif (key not in ignore_fields) and (new_key not in ignore_fields):
                new_dict[new_key] = underscoreize(value, **options)
            else:
                new_dict[new_key] = value

        return new_dict

    if _is_iterable(data) and not isinstance(data, str):
        return [underscoreize(item, **options) for item in data]

    return data


def _is_iterable(obj):
    try:
        _ = iter(obj)
        return True
    except TypeError:
        return False
