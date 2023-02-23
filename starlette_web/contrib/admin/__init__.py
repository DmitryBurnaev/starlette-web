# flake8: noqa

# Mostly copies starlette_admin.contrib.sqla, but without dependency to sqlalchemy_file
# Adds support for own features of starlette_web

from starlette_web.contrib.admin.admin import Admin as __Admin, AdminMount
from starlette_web.contrib.admin.view import ModelView


admin = __Admin()
