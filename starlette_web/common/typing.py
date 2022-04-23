import enum
from typing import TypeVar
from starlette.applications import Starlette


EnumClass = TypeVar("EnumClass", bound=enum.Enum)
AppClass = TypeVar("AppClass", bound=Starlette)
