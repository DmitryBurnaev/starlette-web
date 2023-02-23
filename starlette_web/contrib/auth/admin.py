from starlette_web.contrib.admin import ModelView, admin
from starlette_web.contrib.auth.models import User


class UserView(ModelView):
    fields = []


admin.add_view(UserView(User, icon="fa fa-users"))
