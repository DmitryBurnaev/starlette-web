from starlette_web.common.conf import settings
from starlette_web.common.conf.base_app_config import BaseAppConfig
from starlette_web.common.utils.importing import import_string
from starlette_web.contrib.auth.password_validation import password_validators


class AppConfig(BaseAppConfig):
    app_name = "auth"

    def initialize(self):
        for validator_setting in settings.AUTH_PASSWORD_VALIDATORS:
            validator_class = import_string(validator_setting["BACKEND"])
            options = validator_setting.get("OPTIONS", {})
            validator = validator_class(**options)
            password_validators.append(validator)
