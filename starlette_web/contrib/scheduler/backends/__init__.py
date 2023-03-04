import os
from typing import Type

from starlette_web.common.utils.importing import import_string
from starlette_web.contrib.scheduler.backends.base import BasePeriodicTaskScheduler


def get_periodic_scheduler_backend_class() -> Type[BasePeriodicTaskScheduler]:
    if os.name == "nt":
        return import_string("starlette_web.contrib.scheduler.backends.win32.WindowsTaskScheduler")

    return import_string("starlette_web.contrib.scheduler.backends.posix.CrontabScheduler")
