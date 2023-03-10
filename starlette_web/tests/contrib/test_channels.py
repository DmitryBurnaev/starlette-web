import sys
from subprocess import DEVNULL

import anyio
import pytest

from starlette_web.common.conf import settings
from starlette_web.common.caches import caches
from starlette_web.common.channels.base import Channel, Event
from starlette_web.common.channels.layers.local_memory import InMemoryChannelLayer
from starlette_web.contrib.redis.channel_layers import RedisPubSubChannelLayer
from starlette_web.tests.helpers import await_


class TestChannelLayers:
    # Check both correctness and idempotence of channel layers
    def test_in_memory_channel_layer(self):
        channel_ctx = Channel(InMemoryChannelLayer())
        self.run_channels_test(channel_ctx)
        self.run_channels_test(channel_ctx)
        self.run_channels_test(channel_ctx)

    def test_redis_pubsub_channel_layer(self):
        redis_options = settings.CHANNEL_LAYERS["redispubsub"]["OPTIONS"]
        channel_ctx = Channel(RedisPubSubChannelLayer(**redis_options))
        self.run_channels_test(channel_ctx)
        self.run_channels_test(channel_ctx)
        self.run_channels_test(channel_ctx)

    def run_channels_test(self, channel_ctx):
        accepted_messages = []

        async def publisher_task(channel):
            with anyio.fail_after(2):
                for i in range(5):
                    await anyio.sleep(0.2)
                    await channel.publish("test_group", f"Message {i}")

            # Tests utilize subscribers in an infinite-loop manner,
            # so an outer exception must be raised in order for it to stop.
            # In real application subscribers are expected to be in Websockets,
            # which receive WebsocketDisconnected exception when finished,
            # causing subscriber to stop.
            # This is a mock for tests.
            # Exception will propagate to task group and
            # will close infinite consumers as well.
            await anyio.sleep(0.1)
            raise Exception

        async def subscriber_task(channel, messages_pool):
            async with channel.subscribe("test_group") as subscriber:
                async for message in subscriber:
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
        with pytest.raises(Exception):
            await_(task_coroutine())

        assert len(accepted_messages) == 15
        messages = []
        for event in accepted_messages:
            assert type(event) == Event
            messages.append(event.message)

        for i in range(5):
            assert messages.count(f"Message {i}") == 3

    def test_channels_crossprocess(self):
        test_group_name = "6B65mbrpcAy4zHAjNOZW8T84c7Yl2b"
        subscriber_1 = "Ej3Qu6JFtVbUXh9qb20z"
        subscriber_2 = "Eh9DnQeYvlLI2x5lkMPb"
        subscriber_3 = "ooF5oCaGYAE9dy8aXBSI"

        async def run_command_in_process(command_name, command_args):
            cmd = (
                f"cd {settings.PROJECT_ROOT_DIR} && " 
                f"{sys.executable} command.py {command_name}"
            )

            if command_args:
                cmd += " " + " ".join(command_args)

            async with await anyio.open_process(
                cmd, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL
            ) as process:
                await process.wait()

        async def task_coroutine():
            async with anyio.create_task_group() as nursery:
                nursery.cancel_scope.deadline = anyio.current_time() + 10
                nursery.start_soon(
                    run_command_in_process,
                    "test_channels_publisher",
                    [f"--group={test_group_name}"],
                )
                nursery.start_soon(
                    run_command_in_process,
                    "test_channels_subscriber",
                    [f"--group={test_group_name}", f"--subscriber={subscriber_1}"],
                )
                nursery.start_soon(
                    run_command_in_process,
                    "test_channels_subscriber",
                    [f"--group={test_group_name}", f"--subscriber={subscriber_2}"],
                )
                nursery.start_soon(
                    run_command_in_process,
                    "test_channels_subscriber",
                    [f"--group={test_group_name}", f"--subscriber={subscriber_3}"],
                )

        await_(task_coroutine())

        # TODO: share data via file-cache in tests
        default_cache = caches["default"]
        publisher_flag = await_(default_cache.async_get(f"{test_group_name}-publisher-done"))
        assert publisher_flag == 1

        subscriber_1_flag = await_(
            default_cache.async_get(f"{test_group_name}-{subscriber_1}-done")
        )
        subscriber_2_flag = await_(
            default_cache.async_get(f"{test_group_name}-{subscriber_2}-done")
        )
        subscriber_3_flag = await_(
            default_cache.async_get(f"{test_group_name}-{subscriber_3}-done")
        )
        assert subscriber_1_flag == ["Message 0", "Message 1", "Message 2", "DONE"]
        assert subscriber_2_flag == ["Message 0", "Message 1", "Message 2", "DONE"]
        assert subscriber_3_flag == ["Message 0", "Message 1", "Message 2", "DONE"]
