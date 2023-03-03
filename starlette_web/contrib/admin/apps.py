from importlib import import_module

from starlette_web.common.conf import settings
from starlette_web.common.conf.base_app_config import BaseAppConfig


class AppConfig(BaseAppConfig):
    app_name = "admin"
    app_requirements = [
        "starlette_web.contrib.auth",
        "starlette_web.contrib.staticfiles",
    ]

    def initialize(self):
        for installed_app in settings.INSTALLED_APPS:
            try:
                import_module(installed_app + ".admin")
            except (SystemError, ImportError):
                pass
