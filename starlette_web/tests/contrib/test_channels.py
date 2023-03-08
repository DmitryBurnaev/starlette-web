import anyio
import pytest

from starlette_web.common.conf import settings
from starlette_web.common.channels.base import Channel, Event
from starlette_web.common.channels.layers.local_memory import InMemoryChannelLayer
from starlette_web.common.utils.async_utils import aclosing
from starlette_web.contrib.redis.channel_layers import RedisPubSubChannelLayer
from starlette_web.tests.helpers import await_


class TestChannelLayers:
    def test_in_memory_channel_layer(self):
        channel_ctx = Channel(InMemoryChannelLayer())
        self.run_channels_test(channel_ctx)

    def test_redis_pubsub_channel_layer(self):
        # TODO: get redis configs from elsewhere
        redis_options = settings.CACHES["default"]["OPTIONS"]
        channel_ctx = Channel(RedisPubSubChannelLayer(**redis_options))
        self.run_channels_test(channel_ctx)

    def run_channels_test(self, channel_ctx: Channel):
        accepted_messages = []

        async def publisher_task(channel):
            for i in range(5):
                await anyio.sleep(0.1)
                await channel.publish("test_group", f"Message {i}")

            # Channels is bound to application lifecycle and will loop forever
            # This is a mock for tests, to have it finished earlier
            # Exception will propagate to task group and will close infinite consumers as well
            await anyio.sleep(0.1)
            raise Exception

        async def subscriber_task(channel, messages_pool):
            async with channel.subscribe("test_group") as subscriber:
                async with aclosing(subscriber) as subscriber_wrap:
                    async for message in subscriber_wrap:
                        messages_pool.append(message)

        async def task_coroutine():
            nonlocal accepted_messages

            async with channel_ctx as channels:
                async with anyio.create_task_group() as task_group:
                    task_group.start_soon(publisher_task, channels)
                    task_group.start_soon(subscriber_task, channels, accepted_messages)
                    task_group.start_soon(subscriber_task, channels, accepted_messages)
                    task_group.start_soon(subscriber_task, channels, accepted_messages)

        # Redis will actually raise ExceptionGroup,
        # having 3 subscribers within task group
        # that will raise ConnectionError after close
        with pytest.raises(BaseException):
            await_(task_coroutine())

        assert len(accepted_messages) == 15
        messages = []
        for event in accepted_messages:
            assert type(event) == Event
            messages.append(event.message)

        for i in range(5):
            assert messages.count(f"Message {i}") == 3
