## Caching

Framework supports Django-like generic cache backend.
A sample implementation is provided for RedisCache in `starlette_web.contrib.redis`.

## Plugging-in

- Define the following parameter in your settings.py file:
  - settings.CACHES - a dictionary of dictionaries, containing key `BACKEND` 
  with string import to cache backend, and a key `OPTIONS`, 
  providing whatever options are required to instantiate cache backend.

Example:

```python
CACHES = {
    "default": {
        "BACKEND": "starlette_web.contrib.redis.RedisCache",
        "OPTIONS": {
            "host": "localhost",
            "port": 6379,
            "db": 0,
        },
    }
}
```

## Usage

```python
from starlette_web.common.caches import caches

value = await caches['default'].async_get('key')
await caches['default'].async_set()
```

Default cache is available as `starlette_web.common.caches.cache`.

## Locks

In addition to Django-like cache backend, 
BaseCache implementation provides named locks (mutexes).
Example of usage:

```python
from starlette_web.common.caches import caches

async with caches['default'].lock('lock_name', blocking_timeout=None, timeout=1):
    ...
```