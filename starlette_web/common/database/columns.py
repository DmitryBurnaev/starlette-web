import enum
from typing import Type, TypeVar

import sqlalchemy as sa
from sqlalchemy import Column
from sqlalchemy.sql import type_api as sa_type_api

from starlette_web.common.database.types import ChoiceType


EnumClass = TypeVar("EnumClass", bound=enum.Enum)


class EnumTypeColumn(Column):
    """ Just wrapper for ChoiceType db column

    >>> import enum
    >>> from sqlalchemy import String
    >>> from starlette_web.common.database import ModelBase

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
