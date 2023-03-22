from starlette_web.common.http.exceptions import BaseApplicationError


class ChannelsError(BaseApplicationError):
    pass


class ListenerClosed(ChannelsError):
    pass
