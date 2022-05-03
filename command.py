import sys

from starlette_web.core.app import get_app
from starlette_web.common.management.base import fetch_command_by_name, CommandError


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise CommandError(
            'Missing command name. Correct syntax is: "python command.py command_name ..."'
        )

    command = fetch_command_by_name(sys.argv[1])

    app = get_app()
    command(app).run_from_command_line(sys.argv)
