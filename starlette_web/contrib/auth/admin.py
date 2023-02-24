from starlette_web.contrib.admin import AdminView, admin
from starlette_web.contrib.auth.models import User, UserSession, UserInvite


class UserView(AdminView):
    pass


class UserSessionView(AdminView):
    pass


class UserInviteView(AdminView):
    pass


admin.add_view(UserView(User, icon="fa fa-users"))
admin.add_view(UserSessionView(UserSession, icon="fa fa-database"))
admin.add_view(UserInviteView(UserInvite, icon="fa fa-user-plus"))
