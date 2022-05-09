import os
import sys
import tempfile
from pathlib import Path

from sqlalchemy.engine.url import URL
from starlette.config import Config
from starlette.datastructures import Secret

# TODO: detect real settings path
SETTINGS_PATH = Path(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = Path(os.path.dirname(SETTINGS_PATH))
PROJECT_ROOT_DIR = Path(os.path.dirname(BASE_DIR))

config = Config(PROJECT_ROOT_DIR / ".env")

APP_DEBUG = config("APP_DEBUG", cast=bool, default=False)
SECRET_KEY = config("SECRET_KEY", default="project-secret")

TEST_MODE = "test" in sys.argv[0]

INSTALLED_APPS = [
    "starlette_web.common",
    "starlette_web.tests",
    "starlette_web.contrib.auth",
]

DB_NAME = config("DB_NAME", default="web_project")
if TEST_MODE:
    DB_NAME = config("DB_NAME_TEST", default="web_project_test")

DATABASE = {
    "driver": "postgresql+asyncpg",
    "host": config("DB_HOST", default=None),
    "port": config("DB_PORT", cast=int, default=None),
    "username": config("DB_USERNAME", default=None),
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
    default=URL.create(
        drivername=DATABASE["driver"],
        username=DATABASE["username"],
        password=DATABASE["password"],
        host=DATABASE["host"],
        port=DATABASE["port"],
        database=DATABASE["database"],
    ),
)
DB_ECHO = config("DB_ECHO", cast=bool, default=False)

APPLICATION_CLASS = "starlette_web.common.app.BaseStarletteApplication"

REDIS_HOST = config("REDIS_HOST", default="localhost")
REDIS_PORT = config("REDIS_PORT", default=6379)
REDIS_DB = config("REDIS_DB", default=0)
REDIS_CON = (REDIS_HOST, REDIS_PORT, REDIS_DB)

TMP_PATH = Path(tempfile.mkdtemp(prefix="web_project__"))

JWT_EXPIRES_IN = config("JWT_EXPIRES_IN", default=(5 * 60), cast=int)  # 5 min
JWT_REFRESH_EXPIRES_IN = 30 * 24 * 3600  # 30 days
JWT_ALGORITHM = "HS512"  # see https://pyjwt.readthedocs.io/en/latest/algorithms.html for details

SENDGRID_API_KEY = config("SENDGRID_API_KEY", default="")
SENDGRID_API_VERSION = "v3"
EMAIL_FROM = config("EMAIL_FROM", default="").strip("'\"")
INVITE_LINK_EXPIRES_IN = 3 * 24 * 3600  # 3 day
RESET_PASSWORD_LINK_EXPIRES_IN = 3 * 3600  # 3 hours
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
