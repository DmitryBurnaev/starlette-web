import os
import sys
from typing import Any

from starlette_web.common.http.exceptions import ImproperlyConfigured


class Settings:
    def __init__(self, project_settings):
        self.LOCK_JOBS = self._getattr(project_settings, "PERIODIC_JOBS_LOCK", True)
        self.PERIODIC_JOBS = self._getattr(project_settings, "PERIODIC_JOBS_LIST", [])
        self.PYTHON_EXECUTABLE = self._getattr(
            project_settings, "PERIODIC_JOBS_PYTHON_EXECUTABLE", sys.executable
        )
        self.RUN_DIRECTORY = self._getattr(
            project_settings, "PERIODIC_JOBS_RUN_DIRECTORY", os.getcwd()
        )
        self.SETTINGS_MODULE = self._getattr(project_settings, "STARLETTE_SETTINGS_MODULE", None)
        self.BLOCKING_TIMEOUT = 5

    @staticmethod
    def _getattr(settings: Any, key: str, default: Any) -> Any:
        try:
            return getattr(settings, key)
        except (ImproperlyConfigured, AttributeError):
            return default


class PosixSettings(Settings):
    def __init__(self, project_settings):
        super().__init__(project_settings)
        self.COMMAND_PREFIX = self._getattr(
            project_settings,
            "PERIODIC_JOBS_COMMAND_PREFIX",
            f"cd {self.RUN_DIRECTORY} &&",
        )
        self.COMMAND_SUFFIX = self._getattr(
            project_settings,
            "PERIODIC_JOBS_COMMAND_SUFFIX",
            "",
        )
        self.CRONTAB_EXECUTABLE = self._getattr(
            project_settings,
            "PERIODIC_JOBS_CRONTAB_EXECUTABLE",
            "/usr/bin/crontab",
        )
        self.CRONTAB_LINE_PATTERN = self._getattr(
            project_settings,
            "PERIODIC_JOBS_CRONTAB_LINE_PATTERN",
            "%(time)s %(command)s # %(comment)s",
        )


class Win32Settings(Settings):
    def __init__(self, project_settings):
        super().__init__(project_settings)
        self.USERNAME = self._getattr(
            project_settings,
            "PERIODIC_JOBS_USERNAME",
            "System",
        )
        self.PASSWORD = self._getattr(
            project_settings,
            "PERIODIC_JOBS_PASSWORD",
            None,
        )
