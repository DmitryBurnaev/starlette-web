import base64
import hashlib
import math
from pathlib import Path
import pickle
import re
import tempfile
import time
from typing import AsyncContextManager, Optional, Sequence, Dict, Any, List, BinaryIO, Type

from anyio.lowlevel import checkpoint

from starlette_web.common.conf import settings
from starlette_web.common.caches.base import BaseCache, CacheError
from starlette_web.common.files.filelock import FileLock
from starlette_web.common.http.exceptions import ImproperlyConfigured
from starlette_web.common.utils.regex import redis_pattern_to_re_pattern
from starlette_web.common.utils.serializers import (
    BaseSerializer,
    PickleSerializer,
    DeserializeError,
)


class FileCache(BaseCache):
    # For test purposes, not recommended for production
    lock_class = FileLock
    _manager_lock_blocking_timeout = 10
    _manager_lock_timeout = 1.0
    serializer_class: Type[BaseSerializer] = PickleSerializer
    timestamp_bom = b"ND16C7Bh9Xd"

    def __init__(self, options: Dict[str, Any]):
        super().__init__(options)
        self.base_dir = options.get("CACHE_DIR")
        if self.base_dir is None or not Path(self.base_dir).is_dir():
            raise ImproperlyConfigured(
                details="Invalid CACHE_DIR value for FileCache"
            )
        self.serializer = self.serializer_class()

    async def async_get(self, key: str) -> Any:
        async with self._get_manager_lock():
            return self._sync_get(key)

    async def async_get_many(self, keys: Sequence[str]) -> Dict[str, Any]:
        async with self._get_manager_lock():
            results = {}
            for key in keys:
                await checkpoint()
                results[key] = self._sync_get(key)
            return results

    def _sync_get(self, key: str) -> Any:
        path = Path(self.base_dir) / self._key_name(key)
        if path.is_file():
            with open(path, "rb") as file:
                if self._sync_get_deadline(file) < time.time():
                    return None
                content = self.serializer.deserialize(file.read())
                return content["data"]
        return None

    def _sync_get_deadline(self, _file: BinaryIO) -> float:
        try:
            deadline = _file.read(32)
            if deadline[:11] == self.timestamp_bom:
                # pickle.dumps of float is always 21 bytes
                return pickle.loads(deadline[-21:])
        except DeserializeError:
            _file.seek(0)
            return math.inf

    async def async_set(self, key: str, value: Any, timeout: Optional[float] = 120) -> None:
        async with self._get_manager_lock():
            self._sync_set(key, value, timeout)

    async def async_set_many(self, data: Dict[str, Any], timeout: Optional[float] = 120) -> None:
        async with self._get_manager_lock():
            for key, value in data.items():
                await checkpoint()
                self._sync_set(key, value, timeout)

    def _sync_set(self, key: str, value: Any, timeout: Optional[float] = 120) -> None:
        path = Path(self.base_dir) / self._key_name(key)
        with open(path, "wb") as file:
            content = {"data": value}
            if timeout is not None:
                deadline = time.time() + timeout
                # pickle.dumps of float is always 21 bytes
                file.write(self.timestamp_bom + pickle.dumps(deadline, protocol=4))
            file.write(self.serializer.serialize(content))

    async def async_delete(self, key: str) -> None:
        async with self._get_manager_lock():
            self._sync_delete(key)

    async def async_delete_many(self, keys: Sequence[str]) -> None:
        async with self._get_manager_lock():
            for key in keys:
                self._sync_delete(key)

    def _sync_delete(self, key) -> None:
        path = Path(self.base_dir) / self._key_name(key)
        if path.is_file():
            path.unlink()

    async def async_clear(self) -> None:
        async with self._get_manager_lock():
            _manager_lock_name = self._get_manager_lock_name()
            for file in Path(self.base_dir).iterdir():
                if str(file) == _manager_lock_name:
                    continue
                file.unlink()

    async def async_keys(self, pattern: str) -> List[str]:
        try:
            re_pattern = redis_pattern_to_re_pattern(pattern)
        except re.error as exc:
            raise CacheError(details=str(exc)) from exc

        keys = []
        async with self._get_manager_lock():
            _manager_lock_name = self._get_manager_lock_name()
            for file in Path(self.base_dir).iterdir():
                await checkpoint()
                if str(file) == _manager_lock_name:
                    continue
                key = base64.b32decode(file.name.replace("8", "=").encode()).decode()
                # Check for expiration
                with open(str(file), "rb") as file:
                    deadline = self._sync_get_deadline(file)
                if deadline >= time.time() and re.fullmatch(re_pattern, key):
                    keys.append(key)
            return keys

    async def async_has_key(self, key: str) -> bool:
        return (await self.async_get(key)) is not None

    def _get_manager_lock(self):
        return self.lock_class(
            self._get_manager_lock_name(),
            blocking_timeout=self._manager_lock_blocking_timeout,
            timeout=self._manager_lock_timeout,
        )

    def _get_manager_lock_name(self) -> str:
        return str(Path(tempfile.gettempdir()) / (self._get_project_hash() + '_cache.lock'))

    @staticmethod
    def _key_name(key: str) -> str:
        # 160 base256 => 256 base32
        # Linux supports only 255 bytes for filename,
        # as for Windows, lengthy paths also not recommended
        encoded_key = key.encode("utf-8")
        if len(encoded_key) >= 160:
            raise CacheError(details="Key length exceeds 159 bytes.")

        return base64.b32encode(encoded_key).decode().replace("=", "8")

    def lock(
        self,
        name: str,
        timeout: Optional[float] = 20.0,
        blocking_timeout: Optional[float] = None,
        **kwargs,
    ) -> AsyncContextManager:
        return self.lock_class(
            name=name,
            timeout=timeout,
            blocking_timeout=blocking_timeout,
        )

    def _get_project_hash(self):
        return hashlib.md5(str(settings.SECRET_KEY).encode('utf-8')).hexdigest()
