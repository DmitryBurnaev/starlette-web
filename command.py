import os
import sys

from starlette_web.common.app import get_app
from starlette_web.common.management.base import fetch_command_by_name, CommandError


if __name__ == "__main__":
    settings_module = "starlette_web.core.settings"

    sys_argv = list(sys.argv).copy()
    for arg in sys_argv.copy():
        if arg.startswith("--settings="):
            settings_module = arg[11:]
            sys_argv.remove(arg)

    os.environ.setdefault("STARLETTE_SETTINGS_MODULE", settings_module)

    if len(sys_argv) < 2:
        raise CommandError(
            'Missing command name. Correct syntax is: "python command.py command_name ..."'
        )

    from starlette_web.common.conf import settings

    command = fetch_command_by_name(sys_argv[1])
    app = get_app(use_pool=settings.DB_USE_CONNECTION_POOL_FOR_MANAGEMENT_COMMANDS)
    command(app).run_from_command_line(sys_argv)
