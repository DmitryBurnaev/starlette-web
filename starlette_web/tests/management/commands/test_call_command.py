from starlette_web.common.management.base import BaseCommand, call_command


class Command(BaseCommand):
    help = "Command to test calling other command from code"

    async def handle(self, **options):
        await call_command("test_parser", ["1", "2", "3", "6", "--sum"])
