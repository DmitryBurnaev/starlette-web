import anyio

from starlette_web.common.conf import settings
from starlette_web.common.caches import caches
from starlette_web.common.channels.base import Channel
from starlette_web.common.management.base import BaseCommand
from starlette_web.contrib.redis.channel_layers import RedisPubSubChannelLayer


class Command(BaseCommand):
    help = "Command to cross-process test channels publisher"

    def add_arguments(self, parser):
        parser.add_argument("--group", type=str, required=True)

    async def handle(self, **options):
        group = options["group"]

        redis_options = settings.CHANNEL_LAYERS["redispubsub"]["OPTIONS"]
        channel_ctx = Channel(RedisPubSubChannelLayer(**redis_options))

        with anyio.fail_after(3):
            async with channel_ctx as channel:
                await channel.publish(group, "Message 0")
                await channel.publish(group, "Message 1")
                await channel.publish(group, "Message 2")
                await channel.publish(group, "DONE")

            await caches["default"].async_set(f"{group}-publisher-done", 1, 10)
