from starlette_web.common.conf.base_app_config import BaseAppConfig
from starlette_web.contrib.auth.password_validation import _get_validators


class AppConfig(BaseAppConfig):
    app_name = "auth"

    def initialize(self):
        _get_validators()
