from typing import Dict, Type

from starlette_web.common.conf import settings
from starlette_web.common.channels.base import Channel
from starlette_web.common.channels.exceptions import ChannelsError
from starlette_web.common.channels.layers.base import BaseChannelLayer
from starlette_web.common.utils import import_string


def _create_channels(alias: str) -> Channel:
    try:
        channel_layer_class: Type[BaseChannelLayer] = import_string(
            settings.CHANNEL_LAYERS[alias]["BACKEND"]
        )
        return Channel(channel_layer_class(**settings.CHANNEL_LAYERS[alias]["OPTIONS"]))
    except (ImportError, KeyError) as exc:
        raise ChannelsError from exc


class ChannelLayersHandler:
    def __init__(self):
        self._channels: Dict[str, Channel] = dict()

    def __getitem__(self, alias):
        try:
            return self._channels[alias]
        except KeyError:
            channel_layers = getattr(settings, "CHANNEL_LAYERS", {})
            if alias not in channel_layers:
                raise ChannelsError(f"Channel layer {alias} not in settings.CHANNEL_LAYERS")

            self._channels[alias] = _create_channels(alias)
            return self._channels[alias]


channels = ChannelLayersHandler()
