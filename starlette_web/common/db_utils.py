from typing import Type

import sqlalchemy as sa
from sqlalchemy import types, Column
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import type_api as sa_type_api

from common.typing import EnumClass
from core import settings


class ChoiceType(types.TypeDecorator):
    """
    This implementation taken from https://github.com/kvesteri/sqlalchemy-utils/

    Columns with ChoiceTypes are automatically coerced to Choice objects while
    a list of tuple been passed to the constructor. If a subclass of
    :class:`enum.Enum` is passed, columns will be coerced to value of :class:`enum.Enum`


    >>> import enum
    >>> from core.database import ModelBase
    >>> from sqlalchemy import Column, String

    >>> class UserType(enum.Enum):
    >>>     admin = 'admin'
    >>>     regular = 'regular'

    >>> class User(ModelBase):
    >>>     __tablename__ = 'user'
    >>>     type = Column(ChoiceType(UserType, impl=String(16)))

    >>> user = User(type='admin')
    >>> user.type
    [0] 'admin'

    """

    impl = types.String(255)
    cache_ok = True

    def __init__(self, enum_class, impl=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum_class = enum_class
        if impl:
            self.impl = impl

    def __repr__(self):
        """
        It is used for representation type in alembic logic (render result in mako template)
        migrations.env.render_item uses this representation as "sa.%r" % obj. ex.: "sa.VARCHAR"
        """
        return str(self.impl)

    @property
    def python_type(self):
        return self.impl.python_type

    def coercion_listener(self, target, value, oldvalue, initiator):  # noqa
        return self._coerce(value)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return self.enum_class(value).value

    def process_result_value(self, value, dialect):
        return self._coerce(value)

    def process_literal_param(self, value, dialect):
        return ""

    def _coerce(self, value):
        if value is None:
            return None
        return self.enum_class(value)


class EnumTypeColumn(Column):
    """Just wrapper for ChoiceType db column

    >>> import enum
    >>> from core.database import ModelBase
    >>> from sqlalchemy import String

    >>> class UserType(enum.Enum):
    >>>    admin = 'admin'
    >>>    regular = 'regular'

    >>> class User(ModelBase):
    >>>     ...
    >>>     type = EnumTypeColumn(UserType, impl=String(16), default=UserType.admin)

    >>> user = User(type='admin')
    >>> user.type
    [0] 'admin'

    """

    impl = sa.String(16)

    def __new__(
        cls, enum_class: Type[EnumClass], impl: sa_type_api.TypeEngine = None, *args, **kwargs
    ):
        if "default" in kwargs:
            kwargs["default"] = getattr(kwargs["default"], "value") or kwargs["default"]

        impl = impl or cls.impl
        return Column(ChoiceType(enum_class, impl=impl), *args, **kwargs)


def make_session_maker() -> sessionmaker:
    db_engine = create_async_engine(settings.DATABASE_DSN, echo=settings.DB_ECHO)
    return sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
