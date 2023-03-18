# flake8: noqa

import sys
import tempfile
from pathlib import Path

from starlette.config import Config
from starlette.datastructures import Secret

# TODO: change default project path when running startproject
PROJECT_ROOT_DIR = Path(__file__).parent.parent.parent

config = Config(PROJECT_ROOT_DIR / ".env")

APP_DEBUG = config("APP_DEBUG", cast=bool, default=False)
SECRET_KEY = config("SECRET_KEY", cast=Secret, default="project-secret")

TEST_MODE = "test" in sys.argv[0]

INSTALLED_APPS = [
    "starlette_web.contrib.staticfiles",
    "starlette_web.contrib.apispec",
    "starlette_web.contrib.auth",
    "starlette_web.contrib.admin",
    "starlette_web.contrib.constance.backends.database",
    "starlette_web.contrib.scheduler",
    "starlette_web.tests",
]

DB_ECHO = config("DB_ECHO", cast=bool, default=False)
DB_NAME = config("DB_NAME", default="web_project")
if TEST_MODE:
    DB_NAME = config("DB_NAME_TEST", default="web_project_test")

# TODO: refactor database-specific settings with respect to sqlalchemy.create_engine / asyncpg
DATABASE = {
    "driver": "postgresql+asyncpg",
    "host": config("DB_HOST", default="localhost"),
    "port": config("DB_PORT", cast=int, default=5432),
    "username": config("DB_USERNAME", default="starlette-web"),
    "password": config("DB_PASSWORD", cast=Secret, default=None),
    "database": DB_NAME,
    "pool_min_size": config("DB_POOL_MIN_SIZE", cast=int, default=1),
    "pool_max_size": config("DB_POOL_MAX_SIZE", cast=int, default=16),
    "ssl": config("DB_SSL", default=None),
    "use_connection_for_request": config("DB_USE_CONNECTION_FOR_REQUEST", cast=bool, default=True),
    "retry_limit": config("DB_RETRY_LIMIT", cast=int, default=1),
    "retry_interval": config("DB_RETRY_INTERVAL", cast=int, default=1),
}

DATABASE_DSN = config(
    "DB_DSN",
    cast=str,
    default="{driver}://{username}:{password}@{host}:{port}/{database}".format(**DATABASE),
)

ROUTES = "starlette_web.core.routes.routes"

CACHES = {
    "default": {
        "BACKEND": "starlette_web.contrib.redis.RedisCache",
        "OPTIONS": {
            "host": config("REDIS_HOST", default="localhost"),
            "port": config("REDIS_PORT", default=6379),
            "db": config("REDIS_DB", default=0),
        },
    },
    "locmem": {
        "BACKEND": "starlette_web.common.caches.local_memory.LocalMemoryCache",
        "OPTIONS": {
            "name": "locmem",
        },
    },
}

CHANNEL_LAYERS = {
    "redispubsub": {
        "BACKEND": "starlette_web.contrib.redis.channel_layers.RedisPubSubChannelLayer",
        "OPTIONS": {
            "host": config("REDIS_HOST", default="localhost"),
            "port": config("REDIS_PORT", default=6379),
            "db": config("REDIS_DB", default=0),
        },
    },
}

EMAIL_FROM = config("EMAIL_FROM", default="").strip("'\"")

TMP_PATH = Path(tempfile.mkdtemp(prefix="web_project__"))

SITE_URL = config("SITE_URL", default="") or "https://web.project.com"
SENTRY_DSN = config("SENTRY_DSN", default=None)

LOG_LEVEL = config("LOG_LEVEL", default="INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            "datefmt": "%d.%m.%Y %H:%M:%S",
        },
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "standard"}},
    "loggers": {
        "uvicorn": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "starlette_web": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "common": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
        "app": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
    },
}

TEMPLATES = {
    "ROOT_DIR": PROJECT_ROOT_DIR / "templates",
    "AUTOESCAPE": False,
    "AUTORELOAD": False,
}

STATIC = {
    "ROOT_DIR": PROJECT_ROOT_DIR / "static",
    "URL": "/static/",
}

# TODO: Think about managing permissions
APISPEC = {
    "CONFIG": dict(
        title="Project documentation",
        version="0.0.1",
        openapi_version="3.0.2",
        info=dict(description="My custom project."),
    ),
    "ERROR_RESPONSE_SCHEMA": "starlette_web.common.http.schemas.ErrorResponseSchema",
    "CONVERT_TO_CAMEL_CASE": False,
}
