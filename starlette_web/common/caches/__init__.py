# Copy from https://github.com/django/django/blob/main/django/core/cache/__init__.py

from typing import Dict, Type

from starlette_web.common.caches.base import BaseCache, CacheError
from starlette_web.common.utils import import_string
from starlette_web.core import settings


def _create_cache(alias: str) -> BaseCache:
    try:
        cache_class: Type[BaseCache] = import_string(settings.CACHES[alias]["BACKEND"])
        return cache_class(settings.CACHES[alias]["OPTIONS"])
    except (ImportError, KeyError) as exc:
        raise CacheError from exc


class CacheHandler:
    def __init__(self):
        self._caches: Dict[str, BaseCache] = dict()

    def __getitem__(self, alias):
        try:
            return self._caches[alias]
        except KeyError:
            settings_caches = getattr(settings, "CACHES", {})
            if alias not in settings_caches:
                raise CacheError(f"Cache {alias} not in settings.CACHES")

            self._caches[alias] = _create_cache(alias)
            return self._caches[alias]


caches = CacheHandler()


class DefaultCacheProxy:
    def __getattr__(self, name):
        return getattr(caches["default"], name)

    def __setattr__(self, name, value):
        return setattr(caches["default"], name, value)

    def __delattr__(self, name):
        return delattr(caches["default"], name)

    def __contains__(self, key):
        return key in caches["default"]

    def __eq__(self, other):
        return caches["default"] == other


cache = DefaultCacheProxy()
