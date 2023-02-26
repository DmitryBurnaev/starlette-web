from typing import Any, List, Dict, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette_admin.actions import action
from starlette_admin.exceptions import FormValidationError, ActionFailed

from starlette_web.contrib.admin import AdminView, admin
from starlette_web.contrib.auth.models import User, UserSession, UserInvite


class UserView(AdminView):
    exclude_fields_from_edit = ["password"]
    searchable_fields = ["email"]

    @action(
        name="delete_cascade",
        text="Delete cascade",
        confirmation="Are you sure you want to delete this items?",
        submit_btn_text="Yes, delete them all",
        submit_btn_class="btn-danger",
    )
    async def delete_cascade_action(self, request: Request, pks: List[Any]) -> str:
        affected_rows = await self.delete_users_cascade(request, pks)
        return "{} items were successfully deleted".format(affected_rows)

    @action(
        name="delete",
        text="Delete",
        confirmation="Are you sure you want to delete this items?",
        submit_btn_text="Yes, delete them all",
        submit_btn_class="btn-danger",
    )
    async def delete_action(self, request: Request, pks: List[Any]) -> str:
        try:
            affected_rows = await self.delete(request, pks)
        except SQLAlchemyError as exc:
            raise ActionFailed(str(exc))
        return "{} items were successfully deleted".format(affected_rows)

    async def validate(self, request: Request, data: Dict[str, Any]) -> None:
        # TODO: proper email validation
        # TODO: allow setting password, by hashing it here or in _populate_obj
        errors: Dict[str, str] = {}
        cleaned_email = data["email"].strip()
        if not cleaned_email or "@" not in cleaned_email:
            errors["email"] = "Invalid value for field email."

        if errors:
            raise FormValidationError(errors)
        return await super().validate(request, data)

    async def delete_users_cascade(self, request: Request, pks: List[Any]) -> Optional[int]:
        session: AsyncSession = request.state.session
        objs = await self.find_by_pks(request, pks)

        async with session.begin_nested():
            for obj in objs:
                await UserSession.async_delete(
                    db_session=session,
                    filter_kwargs={"user_id": obj.id},
                )
                await UserInvite.async_delete(
                    db_session=session,
                    filter_kwargs={"user_id": obj.id},
                )
                await session.delete(obj)

        await session.commit()
        return len(objs)


class UserSessionView(AdminView):
    def can_create(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False


class UserInviteView(AdminView):
    def can_create(self, request: Request) -> bool:
        return False

    def can_delete(self, request: Request) -> bool:
        return False


admin.add_view(UserView(User, icon="fa fa-users"))
admin.add_view(UserSessionView(UserSession, icon="fa fa-database"))
admin.add_view(UserInviteView(UserInvite, icon="fa fa-user-plus"))
