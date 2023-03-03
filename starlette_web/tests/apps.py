from starlette_web.common.conf.base_app_config import BaseAppConfig


class AppConfig(BaseAppConfig):
    app_name = "tests"
    app_requirements = [
        "starlette_web.contrib.auth",
    ]
