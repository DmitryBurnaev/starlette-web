import copy
import logging
import os
import tempfile

from starlette_web.contrib.scheduler.backends.base import BasePeriodicTaskScheduler
from starlette_web.contrib.scheduler.app_settings import PosixSettings


logger = logging.getLogger("starlette_web.contrib.scheduler")


class CrontabScheduler(BasePeriodicTaskScheduler):
    settings_class = PosixSettings

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.crontab_lines = []

    def _read_jobs(self):
        self.crontab_lines = os.popen(f"{self.settings.CRONTAB_EXECUTABLE} -l").readlines()

    def _write_jobs(self):
        fd, path = tempfile.mkstemp()
        tmp = os.fdopen(fd, "w")
        for line in self.crontab_lines:
            if not line.strip():
                continue
            tmp.write(line.strip() + "\n")
        tmp.close()
        os.system(f"{self.settings.CRONTAB_EXECUTABLE} {path}")
        os.unlink(path)

    def add_jobs(self):
        project_hash = self._get_project_level_hash()

        for job in self.settings.PERIODIC_JOBS:
            self.crontab_lines.append(
                self.settings.CRONTAB_LINE_PATTERN
                % {
                    "time": job[0],
                    "comment": project_hash,
                    "command": " ".join(
                        filter(
                            None,
                            [
                                self.settings.COMMAND_PREFIX,
                                self.settings.PYTHON_EXECUTABLE,
                                "command.py",
                                "scheduler",
                                "--cmd=run",
                                "--jobhash=" + self._hash_job(job),
                                "--settings=%s" % self.settings.SETTINGS_MODULE,
                                self.settings.COMMAND_SUFFIX,
                            ],
                        )
                    ),
                }
            )

    def show_jobs(self):
        project_hash = self._get_project_level_hash()

        for line in copy.copy(self.crontab_lines):
            if project_hash in line and "crontab run" in line:
                job_hash = line[line.find("crontab run"):][:32]
                job = self._get_job_by_hash(job_hash)
                logger.info(f"{job} -> {line.strip()}")

    def remove_jobs(self):
        project_hash = self._get_project_level_hash()

        for line in copy.copy(self.crontab_lines):
            if project_hash in line:
                self.crontab_lines.remove(line)
