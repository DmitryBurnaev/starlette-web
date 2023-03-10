import anyio

from starlette_web.common.conf import settings
from starlette_web.common.caches import caches
from starlette_web.common.channels.base import Channel
from starlette_web.common.management.base import BaseCommand
from starlette_web.contrib.redis.channel_layers import RedisPubSubChannelLayer


class Command(BaseCommand):
    help = "Command to cross-process test channels subscriber"

    def add_arguments(self, parser):
        parser.add_argument("--group", type=str, required=True)
        parser.add_argument("--subscriber", type=str, required=True)

    async def handle(self, **options):
        group = options["group"]
        subscriber_name = options["subscriber"]
        redis_options = settings.CHANNEL_LAYERS["redispubsub"]["OPTIONS"]
        channel_ctx = Channel(RedisPubSubChannelLayer(**redis_options))

        messages = []

        with anyio.move_on_after(5):
            async with channel_ctx as channel:
                async with channel.subscribe(group) as subscriber:
                    async for event in subscriber:
                        messages.append(event.message)
                        if event.message == "DONE":
                            break

        await caches["default"].async_set(f"{group}-{subscriber_name}-done", messages, 10)
