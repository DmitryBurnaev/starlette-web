import asyncio
from argparse import ArgumentParser
from typing import Optional, List, Type, Awaitable, Dict
from pathlib import Path

from starlette_web.core import settings
from starlette_web.core.app import get_app
from starlette_web.common.utils import import_string


class CommandError(Exception):
    pass


class CommandParser(ArgumentParser):
    """
    Customized ArgumentParser class to improve some error messages and prevent
    SystemExit in several occasions, as SystemExit is unacceptable when a
    command is called programmatically.
    """
    def __init__(self, *, missing_args_message=None, called_from_command_line=None, **kwargs):
        self.called_from_command_line = called_from_command_line
        super().__init__(**kwargs)

    def error(self, message):
        if self.called_from_command_line:
            super().error(message)
        else:
            raise CommandError(message)


class BaseCommand:
    help: Optional[str] = None

    def __init__(self, app):
        self.parser: Optional[CommandParser] = None
        self.app = app

    def create_parser(self, argv, called_from_command_line=True):
        parser = CommandParser(
            prog='%s %s' % (argv[0], argv[1]),
            description=self.help or None,
            called_from_command_line=called_from_command_line,
        )

        return parser

    def add_arguments(self, parser: CommandParser):
        # Redefine in inherited classes
        pass

    async def handle(self, **options):
        raise NotImplementedError

    def prepare_command_coroutine(self, argv, called_from_command_line) -> Awaitable:
        self.parser = self.create_parser(
            argv,
            called_from_command_line=called_from_command_line,
        )
        self.add_arguments(self.parser)
        namespace = self.parser.parse_args(args=argv[2:])
        kwargs = namespace.__dict__
        coroutine = self.handle(**kwargs)
        return coroutine

    def run_from_command_line(self, argv: List[str]):
        coroutine = self.prepare_command_coroutine(argv, True)
        asyncio.get_event_loop().run_until_complete(coroutine)

    async def run_from_code(self, argv: List[str]):
        coroutine = self.prepare_command_coroutine(argv, True)
        await coroutine


def _fetch_commands_and_paths() -> Dict[str, Path]:
    command_files_iter = settings.PROJECT_ROOT_DIR.glob('*/*/management/commands/*.py')
    command_files = {}
    for d in command_files_iter:
        if d.stem in command_files:
            raise CommandError(
                f'Command "{d.stem}" is declared in multiple modules.'
            )
        command_files[d.stem] = d
    return command_files


def list_commands() -> Dict[str, str]:
    commands = _fetch_commands_and_paths()

    return {
        command_name: '.'.join([
            commands[command_name].parent.parent.parent.parent.stem,
            commands[command_name].parent.parent.parent.stem,
            commands[command_name].parent.parent.stem,
            commands[command_name].parent.stem,
            command_name,
            'Command',
        ])
        for command_name, command_path in commands.items()
    }


def fetch_command_by_name(command_name: str) -> Type[BaseCommand]:
    commands = list_commands()

    if command_name in commands:
        try:
            command = import_string(commands[command_name])

            # isinstance not working for class, imported with import_module
            is_instance = any([
                kls
                for kls in command.__mro__
                if kls == BaseCommand
            ])
            if not is_instance:
                raise CommandError(
                    "Command must be inherited from common.management.base.BaseCommand"
                )

            return command
        except (ImportError, AssertionError) as exc:
            raise CommandError from exc

    # TODO: search similarly named commands with ngrams or levenstein distance
    raise CommandError(f'Command "{command_name}" not found.')


async def call_command(command_name, command_args: List[str]):
    command = fetch_command_by_name(command_name)
    app = get_app()
    await command(app).run_from_code(['command.py', command_name] + command_args)
