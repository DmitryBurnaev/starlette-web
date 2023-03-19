import hashlib
import math
import os
import pickle
import sys
import tempfile
import time
from typing import Any, Union, Optional

import anyio
from anyio._core._tasks import TaskGroup
from anyio.lowlevel import checkpoint
from filelock import FileLock as StrictFileLock

from starlette_web.common.conf import settings
from starlette_web.common.caches.base import CacheLockError


class FileLock:
    """
    An async variation of SoftFileLock with support of timeout (via os.path.getmtime)
    """
    EXIT_MAX_DELAY = 60.0

    def __init__(
        self,
        name: Union[str, os.PathLike[Any]],
        timeout: Optional[float] = None,
        blocking_timeout: Optional[float] = None,
    ) -> None:
        self._name = name
        if timeout is None:
            timeout = math.inf
        self._timeout = timeout
        if self._timeout is not None and self._timeout < 0:
            raise RuntimeError("timeout cannot be negative")

        self._blocking_timeout = blocking_timeout
        if self._blocking_timeout is not None and self._blocking_timeout < 0:
            raise RuntimeError("blocking_timeout cannot be negative")

        self._task_group_wrapper: Optional[TaskGroup] = None
        self._task_group: Optional[TaskGroup] = None
        self._acquire_event: Optional[anyio.Event] = None
        self._stored_file_ts = {}
        self._is_acquired = False

    async def __aenter__(self):
        self._task_group_wrapper = anyio.create_task_group()
        self._task_group = await self._task_group_wrapper.__aenter__()
        self._acquire_event = anyio.Event()
        if self._blocking_timeout is not None:
            self._task_group.cancel_scope.deadline = anyio.current_time() + self._blocking_timeout
        self._task_group.start_soon(self._acquire)

        try:
            await self._acquire_event.wait()
            self._is_acquired = self._acquire_event.is_set()
        except anyio.get_cancelled_exc_class() as exc:
            await self._task_group_wrapper.__aexit__(*sys.exc_info())
            self._is_acquired = False
            raise CacheLockError(details=str(exc)) from exc

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._acquire_event = None
        retval = await self._task_group_wrapper.__aexit__(exc_type, exc_val, exc_tb)
        with anyio.move_on_after(self.EXIT_MAX_DELAY, shield=True):
            await self._release()

        if self._task_group.cancel_scope.cancel_called:
            raise CacheLockError(
                details=f"Could not acquire FileLock within {self._timeout} seconds."
            ) from exc_val

        self._task_group = None
        self._task_group_wrapper = None
        return retval

    async def _acquire(self):
        if self._is_acquired:
            return

        while True:
            await checkpoint()
            try:
                with self._get_manager_lock():
                    if self._sync_acquire():
                        self._acquire_event.set()
                        return
            except OSError:
                continue

    async def _release(self):
        if not self._is_acquired:
            return

        while True:
            await checkpoint()
            try:
                with self._get_manager_lock():
                    self._sync_release()
                    return
            except OSError:
                continue

    def _sync_release(self):
        try:
            ts = os.path.getmtime(self._name)
            # Another process has re-acquired lock due to timeout
            if ts not in self._stored_file_ts:
                return
            os.unlink(self._name)
        finally:
            self._stored_file_ts = {}
            self._is_acquired = False

    def _sync_acquire(self) -> bool:
        if os.path.exists(self._name):
            ts = os.path.getmtime(self._name)

            if ts not in self._stored_file_ts:
                with open(self._name, "rb") as file:
                    self._stored_file_ts[ts] = pickle.loads(file.read())

            # Timeout on other instance has not expired
            if self._stored_file_ts[ts] + ts > time.time():
                return False

            # Timeout for lock has expired, so we acquire it.
            # Remove lock file to update its mtime
            self._sync_release()

        with open(self._name, "wb+") as file:
            file.write(pickle.dumps(self._timeout, protocol=4))
            # Guarantee that writing is finalized
            file.flush()
            os.fsync(file.fileno())

        ts = os.path.getmtime(self._name)
        self._stored_file_ts[ts] = self._timeout
        return True

    def __del__(self):
        try:
            self._sync_release()
        except OSError:
            pass

    def _get_manager_lock(self):
        _manager_lock_filepath = os.path.join(
            tempfile.gettempdir(),
            self._get_project_hash() + "_filelock.lock",
        )
        # timeout=0 means exactly 1 attempt to acquire lock
        return StrictFileLock(_manager_lock_filepath, timeout=0)

    def _get_project_hash(self):
        return hashlib.md5(str(settings.SECRET_KEY).encode('utf-8')).hexdigest()
