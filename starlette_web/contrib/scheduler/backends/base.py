import json
import hashlib
import logging
import os
import tempfile
from typing import List, Dict, Tuple, TypeAlias, Union

import anyio
from filelock import FileLock
from traceback_with_variables import format_exc

from starlette_web.common.conf import settings as project_settings

# Scheduler is only supposed to be run as management-command
from starlette_web.common.management.base import CommandError
from starlette_web.common.utils.importing import import_string
from starlette_web.contrib.scheduler.app_settings import Settings


logger = logging.getLogger("starlette_web.contrib.scheduler")
JSONType: TypeAlias = Union[
    Dict[str, "JSONType"],
    List["JSONType"],
    str,
    int,
    float,
    bool,
    None,
]
# Arguments:
# [0] crontab-like schedule (including @reboot)
# [1] import string for async function to be executed
# [2] args
# [3] kwargs
# [4] timeout
JobType = Tuple[str, str, List[JSONType], Dict[str, JSONType], Union[float, None]]


class BasePeriodicTaskScheduler:
    settings_class = Settings

    def __init__(self, **kwargs):
        self.needs_read = kwargs.get("needs_read", True)
        self.needs_write = kwargs.get("needs_write", True)
        self.settings = self.settings_class(project_settings)

    def __enter__(self):
        if self.needs_read:
            self._read_jobs()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.needs_write:
            self._write_jobs()
        return False

    def _read_jobs(self):
        raise CommandError("Not supported for this platform.")

    def _write_jobs(self):
        raise CommandError("Not supported for this platform.")

    def add_jobs(self):
        raise CommandError("Not supported for this platform.")

    def update_jobs(self):
        self.remove_jobs()
        self.add_jobs()

    def show_jobs(self):
        raise CommandError("Not supported for this platform.")

    def remove_jobs(self):
        raise CommandError("Not supported for this platform.")

    async def run_job(self, job_hash: str):
        cron_pattern, async_func, job_args, job_kwargs, timeout = self._get_job_by_hash(job_hash)
        async_job_handler = import_string(async_func)

        with self._get_job_mutex(job_hash):
            with anyio.CancelScope() as cancel_scope:
                if timeout is not None:
                    cancel_scope.deadline = anyio.current_time() + timeout

                try:
                    await async_job_handler(*job_args, **job_kwargs)
                except Exception as exc:
                    logger.critical(format_exc(exc))

    def _get_project_level_hash(self) -> str:
        return hashlib.md5(str(project_settings.SECRET_KEY).encode("utf-8")).hexdigest()

    def _hash_job(self, job: JobType) -> str:
        job_string = json.JSONEncoder(sort_keys=True).encode(job)
        job_hash = hashlib.md5(job_string.encode("utf-8")).hexdigest()
        return job_hash

    def _get_job_by_hash(self, job_hash: str) -> JobType:
        for job in self.settings.PERIODIC_JOBS:
            if self._hash_job(job) == job_hash:
                return job

        raise CommandError(details=f"Periodic job with hash = {job_hash} not found.")

    def _get_job_mutex(self, job_hash: str):
        if self.settings.LOCK_JOBS:
            lock_file = os.path.join(
                tempfile.gettempdir(), self._get_project_level_hash() + "_" + job_hash + ".lock"
            )
            return FileLock(lock_file, timeout=self.settings.BLOCKING_TIMEOUT)
        else:

            class DummyLock:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc_val, exc_tb):
                    return False

            return DummyLock()
