from starlette.requests import Request
from starlette.types import Scope

from starlette_web.contrib.auth.models import User
from starlette_web.common.authorization.permissions import BasePermission
from starlette_web.common.http.exceptions import PermissionDeniedError


class IsSuperuserPermission(BasePermission):
    async def has_permission(self, request: Request, scope: Scope) -> bool:
        user: User = scope.get("user")
        if (not user) or (not getattr(user, "is_superuser", False)):
            raise PermissionDeniedError(details="You don't have an admin privileges.")

        return True
