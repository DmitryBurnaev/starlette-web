import ctypes
import datetime
import json
import logging
import warnings

import croniter
from py_win_task_scheduler import (
    list_folders,
    create_folder,
    list_tasks,
    info as get_task_info,
    create_task,
    delete_task,
)

from starlette_web.common.management.base import CommandError
from starlette_web.contrib.scheduler.backends.base import BasePeriodicTaskScheduler
from starlette_web.contrib.scheduler.app_settings import Win32Settings


logger = logging.getLogger("starlette_web.contrib.scheduler")


class WindowsTaskScheduler(BasePeriodicTaskScheduler):
    settings_class = Win32Settings

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._project_folder_exists = False
        self._current_jobs = []
        self._root_dir = "starlette_web"

    def __enter__(self):
        if self.needs_write:
            if ctypes.windll.shell32.IsUserAnAdmin() == 0:
                warnings.warn(
                    "You may have insufficient privileges to make "
                    "changes to Task Scheduler as non-administrator"
                )

        self._ensure_project_folder_exists()
        self._read_jobs()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def _read_jobs(self):
        project_hash = self._get_project_level_hash()
        location = "\\" + self._root_dir + "\\" + project_hash
        self._current_jobs = list_tasks(location=location)

    def update_jobs(self):
        all_jobs = [self._hash_job(job) for job in self.settings.PERIODIC_JOBS]
        jobs_to_add = set(all_jobs) - set(self._current_jobs)
        jobs_to_delete = set(self._current_jobs) - set(all_jobs)

        project_hash = self._get_project_level_hash()
        location = "\\" + self._root_dir + "\\" + project_hash

        for job_hash in jobs_to_delete:
            deleted = delete_task(job_hash, location=location)
            if not deleted:
                raise CommandError(f"Could not delete task {job_hash}")

            logger.info(f"Removing scheduled task {job_hash}")

        for job_hash in jobs_to_add:
            job = self._get_job_by_hash(job_hash)

            if job[0] == "@reboot":
                schedule_kwargs = dict(
                    trigger_type="OnBoot",
                )
            else:
                # Add 5 seconds to ensure Windows has time to prepare entry in scheduler registry
                now = datetime.datetime.now().astimezone() + datetime.timedelta(seconds=5)
                it = croniter.croniter("* * * * *", now)
                start_dt = datetime.datetime.fromtimestamp(next(it)).astimezone()
                start_time = start_dt.time().strftime("%H:%M")
                start_date = start_dt.date().strftime("%Y-%m-%d")

                schedule_kwargs = dict(
                    trigger_type="Daily",
                    repeat_interval="1 minute",
                    repeat_duration="1 day",
                    start_time=start_time,
                    start_date=start_date,
                )

            created = create_task(
                name=job_hash,
                location=location,
                description=f"Periodic job {job_hash}",
                enabled=True,
                hidden=False,
                user_name=self.settings.USERNAME,
                password=self.settings.PASSWORD,
                run_if_idle=False,
                ac_only=False,
                stop_if_on_batteries=False,
                wake_to_run=True,
                run_if_network=False,
                allow_demand_start=False,
                start_when_available=True,
                force=True,
                restart_every=False,
                execution_time_limit=False,
                force_stop=True,
                delete_after=False,
                multiple_instances=not self.settings.LOCK_JOBS,
                action_type="Execute",
                cmd=self.settings.PYTHON_EXECUTABLE,
                arguments=(
                    f"command.py "
                    f"scheduler "
                    f"run "
                    f"{job_hash} "
                    f"--settings={self.settings.SETTINGS_MODULE}"
                ),
                start_in=self.settings.RUN_DIRECTORY,
                **schedule_kwargs,
            )
            if not created:
                raise CommandError(message=f"Could not create task {job}")

            logger.info(f"Created scheduled task {job}")

    def _ensure_project_folder_exists(self):
        if self._project_folder_exists:
            return

        root_folders = list_folders("\\")
        if self._root_dir not in root_folders:
            created = create_folder(self._root_dir, location="\\")
            if not created:
                raise CommandError(
                    details="Root folder for project scheduled tasks "
                    "could not be created with Task Scheduler 2.0"
                )

        project_hash = self._get_project_level_hash()
        projects_folders = list_folders("\\" + self._root_dir)
        if project_hash not in projects_folders:
            created = create_folder(project_hash, location="\\" + self._root_dir)
            if not created:
                raise CommandError(
                    details="Root folder for project scheduled tasks "
                    "could not be created with Task Scheduler 2.0"
                )

        self._project_folder_exists = True

    async def run_job(self, job_hash: str):
        job = self._get_job_by_hash(job_hash)

        # Windows jobs actually run every minute, since there is no easy
        # way to support crontab syntax. Instead, we check it here.
        if job[0] != "@reboot":
            now = datetime.datetime.now().astimezone() - datetime.timedelta(seconds=5)
            next_run_ts = next(croniter.croniter(job[0], now))
            if (
                datetime.datetime.fromtimestamp(next_run_ts).astimezone() - now
            ).total_seconds() > 30:
                return

        return await super().run_job(job_hash)

    def show_jobs(self):
        project_hash = self._get_project_level_hash()
        location = "\\" + self._root_dir + "\\" + project_hash

        for job in self.settings.PERIODIC_JOBS:
            task_name = self._hash_job(job)
            if task_name in self._current_jobs:
                task_info = get_task_info(task_name, location=location)
                logger.info("%s -> %s" % (job, location + task_name))
                logger.info(json.dumps(task_info, indent=2))

    def remove_jobs(self):
        project_hash = self._get_project_level_hash()
        location = "\\" + self._root_dir + "\\" + project_hash

        for job_hash in self._current_jobs:
            deleted = delete_task(name=job_hash, location=location)

            if not deleted:
                raise CommandError(
                    details=f"Task {job_hash} for project scheduled tasks "
                    "could not be deleted with Task Scheduler 2.0"
                )
