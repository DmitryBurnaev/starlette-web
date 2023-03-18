# Core application settings

APP_DEBUG = False
APPLICATION_CLASS = "starlette_web.tests.app.TestStarletteApplication"

SECRET_KEY = ""
INSTALLED_APPS = []
MIDDLEWARES = []

LOG_LEVEL = "INFO"
LOGGING = {}

# TODO: for future support of i18n
LANGUAGE_CODE = "en-us"

# Database settings

DB_ASYNC_SESSION_CLASS = "sqlalchemy.ext.asyncio.AsyncSession"
DB_USE_CONNECTION_POOL_FOR_MANAGEMENT_COMMANDS = False
DB_POOL_RECYCLE = 3600

# Common.cache

CACHES = {
    "default": {
        "BACKEND": "starlette_web.common.caches.local_memory.LocalMemoryCache",
        "OPTIONS": {
            "name": "default",
        },
    },
}

# Common.email

# TODO: copy other email-relevant options in SMTPproto issue
# https://github.com/django/django/blob/main/django/conf/global_settings.py#L190
EMAIL_SENDER = None
EMAIL_FROM = ""

# Contrib.auth

AUTH_PASSWORD_HASHERS = [
    "starlette_web.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"BACKEND": "starlette_web.contrib.auth.password_validation.NumericPasswordValidator"},
    {"BACKEND": "starlette_web.contrib.auth.password_validation.PasswordLengthValidator"},
    {"BACKEND": "starlette_web.contrib.auth.password_validation.UsernameSimilarityValidator"},
]

AUTH_JWT_EXPIRES_IN = 300  # 5 min
AUTH_JWT_REFRESH_EXPIRES_IN = 30 * 24 * 3600  # 30 days
AUTH_JWT_ALGORITHM = "HS512"  # see https://pyjwt.readthedocs.io/en/latest/algorithms.html for details
AUTH_INVITE_LINK_EXPIRES_IN = 3 * 24 * 3600  # 3 day
AUTH_RESET_PASSWORD_LINK_EXPIRES_IN = 3 * 3600  # 3 hours
