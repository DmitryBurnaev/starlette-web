## About Constance

Constance is a port of django-constance library for django, implemented as a contrib library.
It is a key-value storage for global project-level constants, which can use various underlying backends.

## Plugging-in

- Define 2 settings in your settings.py-file:
  - settings.CONSTANCE_BACKEND - `str` - a string with path to constance backend class, i.e. "starlette_web.contrib.constance.backends.database.DatabaseBackend"
  - settings.CONSTANCE_CONFIG - `Dict[str, Tuple[Any, str, Type]]` - a dict, where keys are constant keys, and value is a 3-value tuple (default value, description, type)
