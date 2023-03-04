from importlib import import_module
import os
from typing import Dict, Any

from starlette_web.common.http.exceptions import ImproperlyConfigured


_getattr = object.__getattribute__
_setattr = object.__setattr__
empty = object()


class Settings:
    ENVIRONMENT_VARIABLE = "STARLETTE_SETTINGS_MODULE"
    _global_settings: Dict[str, Any]
    _user_settings: Dict[str, Any]
    _setup_done: bool

    def __init__(self):
        _setattr(self, "_global_settings", dict())
        _setattr(self, "_user_settings", dict())
        _setattr(self, "_setup_done", False)

    def _setup(self) -> None:
        settings_module = os.environ.get(_getattr(self, "ENVIRONMENT_VARIABLE"))
        if not settings_module:
            raise ImproperlyConfigured(
                details="Environment variable STARLETTE_SETTINGS_MODULE is not configured."
            )

        module = import_module(settings_module)
        for setting in dir(module):
            if setting.isupper():
                setting_value = getattr(module, setting)
                _getattr(self, "_user_settings")[setting] = setting_value

        _getattr(self, "_user_settings")["STARLETTE_SETTINGS_MODULE"] = settings_module
        _setattr(self, "_setup_done", True)

    def __getattr__(self, key: str) -> Any:
        if not _getattr(self, "_setup_done"):
            _getattr(self, "_setup")()

        value = _getattr(self, "_user_settings").get(key, empty)
        if value is empty:
            raise ImproperlyConfigured(details=f"Setting {key.upper()} is not configured.")

        return value

    def __setattr__(self, key: str, value: Any) -> None:
        _getattr(self, "_user_settings")[key.upper()] = value


settings = Settings()
