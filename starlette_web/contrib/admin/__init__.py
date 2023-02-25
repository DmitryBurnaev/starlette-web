# flake8: noqa

from starlette_web.contrib.admin.view import ModelView as AdminView
from starlette_web.contrib.admin.admin import Admin as _Admin, AdminMount


admin = _Admin()
