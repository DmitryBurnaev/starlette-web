## Channels (Pub-sub)

Channels is a common module in `starlette_web`, designed to provide a pub-sub functionality.
It is named after `django-channels`, however is based off `https://github.com/encode/broadcaster`.
The core is adapted to `anyio`.

The exact type of delivering message is based on underlying channel layer, and may either require
acknowledge, or be fire-and-forget.

Supported channel layers:

- `starlette_web.common.channels.layers.local_memory.InMemoryChannelLayer` -single-process, for testing
- `starlette_web.contrib.redis.channel_layers.RedisPubSubChannelLayer` - cross-process fire-and-forget layer

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

## Known issues

Channels cannot be used project-globally in the same way, as caches are, 
but have to be instantiated every time you want to use them, with `async with` block.
In `channels`, the channel layer is instantiated for the whole duration of `async with` block,
and holds a set of memory streams, which it uses to fire messages to subscribers.
**Subscribers may be instantiated in a different thread**, than the main application, 
which goes against the fact that all `anyio` operations **are not threadsafe**.

The exact reason boils down to the fact, that async Queues depend on async Events, 
which do not function between different event-loops/threads. A cross-thread/cross-event-loop
pub-sub would require using synchronous `threading.Queue` instead, which is out of scope of
responsibility of `starlette_web.common.channels`.

In comparison, this is not an issue for caches, since all operations in caches are atomic
and do not require pair-wise synchronization.

In practice, this means, that you have to instantiate channels every time you need to use them.
