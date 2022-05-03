from starlette_web.common.utils import import_string
from starlette_web.core import settings


def get_app():
    StarletteApplication = import_string(settings.APPLICATION_CLASS)
    return StarletteApplication().get_app()
