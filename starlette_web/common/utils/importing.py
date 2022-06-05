from importlib import import_module
from typing import Any


def import_string(dotted_path) -> Any:
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % dotted_path) from err

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        error_description = 'Module "%s" does not define a "%s" attribute/class' % (
            module_path,
            class_name,
        )
        raise ImportError(error_description) from err
