## Channels (Pub-sub)

Channels is a common module in `starlette_web`, designed to provide a pub-sub functionality.
It is named after `django-channels`, however is based off `https://github.com/encode/broadcaster`.
The core is adapted to `anyio`, whereas underlying channel layers may depend on `asyncio`-based libraries.

The exact type of delivering pipeline is based on underlying channel layer, and may either require
acknowledgement, or be fire-and-forget.

Supported channel layers:

- `starlette_web.common.channels.layers.local_memory.InMemoryChannelLayer` -single-process, fire-and-forget, for testing
- `starlette_web.contrib.redis.channel_layers.RedisPubSubChannelLayer` - cross-process, fire-and-forget
- `starlette_web.contrib.postgres.channel_layers.PostgreSQLChannelLayer` - cross-process, fire-and-forget

## Example

```python3
from starlette_web.common.channels.base import Channel
from starlette_web.common.channels.layers.local_memory import InMemoryChannelLayer

async with Channel(InMemoryChannelLayer()) as channel:
    await channel.publish("chatroom", {"message": "Message"})
    ...
    async with channel.subscribe("chatroom") as subscribe:
        # This is infinite iterator, so use it in a scope, where it can be cancelled/stopped
        # i.e. websockets, anyio.move_on_after, or simply with an exiting message
        async for event in subscribe:
            await process_event(event)
```

## Subscribing to multiple groups/channels

Currently, this not implemented for default channel layers, 
since different brokers support such behavior differently, 
and some do not support at all. 
You may define a custom channel layer for this purpose. Example:

```python3
from starlette_web.contrib.redis.channel_layers import RedisPubSubChannelLayer


class RedisMultipleChannelLayer(RedisPubSubChannelLayer):
    def subscribe(self, groups: str) -> None:
        groups = groups.split(";")
        # Redis SUBSCRIBE command accepts multiple arguments
        # https://redis.io/commands/subscribe/
        await self._pubsub.subscribe(*groups)

    def unsubscribe(self, groups: str) -> None:
        groups = groups.split(";")
        # Redis UNSUBSCRIBE command accepts multiple arguments
        # https://redis.io/commands/unsubscribe/
        await self._pubsub.unsubscribe(*groups)


class RedisMultiplePatternsChannelLayer(RedisPubSubChannelLayer):
    def subscribe(self, patterns: str) -> None:
        patterns = patterns.split(";")
        # https://redis.io/commands/psubscribe/
        await self._pubsub.psubscribe(*patterns)

    def unsubscribe(self, patterns: str) -> None:
        patterns = patterns.split(";")
        # https://redis.io/commands/punsubscribe/
        await self._pubsub.punsubscribe(*patterns)
```

## Known issues

Channels cannot be instantiated project-wise, in the same way as caches.
In `channels`, the channel layer is instantiated for the whole duration of `async with` block,
and holds a set of memory streams, which it uses to fire messages to subscribers.
**Subscribers may be instantiated in a different thread**, then the main application, 
which goes against the fact that all `anyio` operations are **by-design not threadsafe**.

The exact reason boils down to the fact, that async Queues, which are used for synchronization,
depend on async Events, which do not function between different event-loops/threads. 
A cross-thread/cross-event-loop pub-sub would require using synchronous `threading.Queue` instead, 
which is out of scope of responsibility of `starlette_web.common.channels`.

In comparison, this is not an issue for caches, since all operations in caches are atomic
and do not require pair-wise synchronization.

In practice, this means, that you have to instantiate channels with `async with` block, 
every time you need to use them. See `starlette_web.tests.contrib.test_channels.TestChannelLayers`
for examples of usage.
