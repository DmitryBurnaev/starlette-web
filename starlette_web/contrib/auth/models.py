import secrets
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession

from starlette_web.common.database import ModelMixin, ModelBase
from starlette_web.common.authorization.base_user import BaseUser
from starlette_web.contrib.auth.hashers import make_password, verify_password


class User(ModelBase, BaseUser, ModelMixin):
    __tablename__ = "auth_users"

    id = Column(Integer, primary_key=True)
    email = Column(String(length=128), index=True, nullable=False, unique=True)
    password = Column(String(length=256), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    class Meta:
        order_by = ("id",)

    def __repr__(self):
        return f"<User #{self.id} {self.email}>"

    @classmethod
    def make_password(cls, raw_password: str) -> str:
        return make_password(raw_password)

    def verify_password(self, raw_password: str) -> bool:
        return verify_password(raw_password, str(self.password))

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return self.email

    @classmethod
    async def get_active(cls, db_session: AsyncSession, user_id: int) -> "User":
        return await cls.async_get(db_session, id=user_id, is_active=True)


class UserInvite(ModelBase, ModelMixin):
    __tablename__ = "auth_invites"
    TOKEN_MAX_LENGTH = 32

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("auth_users.id"), unique=True)
    email = Column(String(length=128), unique=True)
    token = Column(String(length=32), unique=True, nullable=False, index=True)
    is_applied = Column(Boolean, default=False, nullable=False)
    expired_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    owner_id = Column(Integer, ForeignKey("auth_users.id"), nullable=False)

    class Meta:
        order_by = ("id",)

    def __repr__(self):
        return f"<UserInvite #{self.id} {self.token}>"

    @classmethod
    def generate_token(cls):
        return secrets.token_urlsafe()[: cls.TOKEN_MAX_LENGTH]


class UserSession(ModelBase, ModelMixin):
    __tablename__ = "auth_sessions"

    id = Column(Integer, primary_key=True)
    public_id = Column(String(length=36), index=True, nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("auth_users.id"))
    refresh_token = Column(String(length=512))
    is_active = Column(Boolean, default=True, nullable=False)
    expired_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    refreshed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    class Meta:
        order_by = ("id",)

    def __repr__(self):
        return f"<UserSession #{self.id} {self.user_id}>"
