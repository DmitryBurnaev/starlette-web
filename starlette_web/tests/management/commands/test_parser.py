from starlette_web.common.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Command to test command line arguments'

    def add_arguments(self, parser):
        parser.add_argument(
            'integers',
            metavar='N',
            type=int,
            nargs='+',
            help='an integer for the accumulator',
        )
        parser.add_argument(
            '--sum',
            dest='accumulate',
            action='store_const',
            const=sum,
            default=max,
            help='sum the integers (default: find the max)',
        )

    async def handle(self, **options):
        print(options['accumulate'](options['integers']))
