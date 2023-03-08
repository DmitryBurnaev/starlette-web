from starlette_web.common.http.exceptions import BaseApplicationError


class ChannelsError(BaseApplicationError):
    pass


class Unsubscribed(ChannelsError):
    message = "Subscriber unsubscribed from group."


class ListenerClosed(ChannelsError):
    pass
