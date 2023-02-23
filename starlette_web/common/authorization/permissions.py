# Copied from https://github.com/encode/django-rest-framework/blob/master/rest_framework/permissions.py  # noqa E501

from typing import Type, Union

from starlette.requests import Request
from starlette.types import Scope

from starlette_web.common.authorization.base_user import BaseUserMixin


class OperationHolderMixin:
    def __and__(self, other):
        return OperandHolder(AND, self, other)

    def __or__(self, other):
        return OperandHolder(OR, self, other)

    def __rand__(self, other):
        return OperandHolder(AND, other, self)

    def __ror__(self, other):
        return OperandHolder(OR, other, self)

    def __invert__(self):
        return SingleOperandHolder(NOT, self)


class SingleOperandHolder(OperationHolderMixin):
    def __init__(self, operator_class, op1_class):
        self.operator_class = operator_class
        self.op1_class = op1_class

    def __call__(self, *args, **kwargs):
        op1 = self.op1_class(*args, **kwargs)
        return self.operator_class(op1)


class OperandHolder(OperationHolderMixin):
    def __init__(self, operator_class, op1_class, op2_class):
        self.operator_class = operator_class
        self.op1_class = op1_class
        self.op2_class = op2_class

    def __call__(self, *args, **kwargs):
        op1 = self.op1_class(*args, **kwargs)
        op2 = self.op2_class(*args, **kwargs)
        return self.operator_class(op1, op2)


class AND:
    def __init__(self, op1, op2):
        self.op1 = op1
        self.op2 = op2

    async def has_permission(self, request: Request, scope: Scope):
        return (await self.op1.has_permission(request, scope)) and (
            await self.op2.has_permission(request, scope)
        )


class OR:
    def __init__(self, op1, op2):
        self.op1 = op1
        self.op2 = op2

    async def has_permission(self, request: Request, scope: Scope):
        return (await self.op1.has_permission(request, scope)) or (
            await self.op2.has_permission(request, scope)
        )


class NOT:
    def __init__(self, op1):
        self.op1 = op1

    async def has_permission(self, request: Request, scope: Scope):
        return not (await self.op1.has_permission(request, scope))


class BasePermissionMetaclass(OperationHolderMixin, type):
    pass


class BasePermission(metaclass=BasePermissionMetaclass):
    async def has_permission(self, request: Request, scope: Scope) -> bool:
        raise NotImplementedError


class AllowAnyPermission(BasePermission):
    async def has_permission(self, request: Request, scope: Scope) -> bool:
        return True


class IsAuthenticatedPermission(BasePermission):
    async def has_permission(self, request: Request, scope: Scope) -> bool:
        if "user" not in scope:
            return False

        user: BaseUserMixin = scope["user"]
        return user.is_authenticated


PermissionType = Union[Type[BasePermission], OperandHolder]
