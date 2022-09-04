from apispec.ext.marshmallow import MarshmallowPlugin

from starlette_web.common.apispec.marshmallow.converters import (
    StarletteWebMarshmallowOpenAPIConverter,
)


# TODO: maybe allow user to override class in settings (?)
class StarletteWebMarshmallowPlugin(MarshmallowPlugin):
    Converter = StarletteWebMarshmallowOpenAPIConverter
