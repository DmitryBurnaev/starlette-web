import logging

from starlette_web.common.management.base import BaseCommand, CommandParser
from starlette_web.contrib.scheduler.backends import get_periodic_scheduler_backend_class


logger = logging.getLogger("starlette_web.contrib.scheduler")


class Command(BaseCommand):
    help = "Manage periodic jobs with OS-wide task scheduler"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument(
            "cmd", choices=["add", "show", "remove", "run"], type=str, required=True
        )
        parser.add_argument("jobhash", type=str, required=False)

    async def handle(self, **options):
        scheduler_class = get_periodic_scheduler_backend_class()

        if options["cmd"] == "add":
            with scheduler_class(needs_read=True, needs_write=True) as scheduler:
                scheduler.update_jobs()

        elif options["cmd"] == "remove":
            with scheduler_class(needs_read=True, needs_write=True) as scheduler:
                scheduler.remove_jobs()

        elif options["cmd"] == "show":
            with scheduler_class(needs_read=True, needs_write=False) as scheduler:
                scheduler.show_jobs()

        elif options["cmd"] == "run":
            with scheduler_class(needs_read=False, needs_write=False) as scheduler:
                await scheduler.run_job(options["jobhash"])

        else:
            logger.warning(self.help)
