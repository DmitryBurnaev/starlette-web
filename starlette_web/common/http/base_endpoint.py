import logging
import sys
from typing import Type, Union, Iterable, ClassVar, Optional, Mapping, List, Any, Dict

from marshmallow import Schema, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.background import BackgroundTasks
from starlette.exceptions import HTTPException
from starlette.endpoints import HTTPEndpoint
from starlette.requests import Request
from webargs_starlette import WebargsHTTPException, StarletteParser

from starlette_web.common.app import WebApp
from starlette_web.common.authorization.backends import (
    BaseAuthenticationBackend,
    NoAuthenticationBackend,
)
from starlette_web.common.authorization.permissions import PermissionType
from starlette_web.common.authorization.base_user import AnonymousUser
from starlette_web.common.http.exceptions import (
    UnexpectedError,
    BaseApplicationError,
    InvalidParameterError,
    PermissionDeniedError,
)
from starlette_web.common.http.renderers import BaseRenderer, JSONRenderer
from starlette_web.common.http.statuses import ResponseStatus
from starlette_web.common.database import DBModel


logger = logging.getLogger(__name__)


class BaseHTTPEndpoint(HTTPEndpoint):
    """
    Base View witch used as a base class for every API's endpoints
    """

    app = None
    request: Request
    db_session: AsyncSession
    db_model: ClassVar[DBModel]
    request_schema: ClassVar[Type[Schema]]
    response_schema: ClassVar[Type[Schema]]
    auth_backend: ClassVar[Type[BaseAuthenticationBackend]] = NoAuthenticationBackend
    permission_classes: ClassVar[List[PermissionType]] = []
    request_parser: ClassVar[Type[StarletteParser]] = StarletteParser
    response_renderer: ClassVar[Type[BaseRenderer]] = JSONRenderer

    async def dispatch(self) -> None:
        """
        This method is calling in every request.
        So, we can use this one for customs authenticate and catch all exceptions
        """

        self.request = Request(self.scope, receive=self.receive)
        self.app: WebApp = self.scope.get("app")

        handler_name = "get" if self.request.method == "HEAD" else self.request.method.lower()
        handler = getattr(self, handler_name, self.method_not_allowed)

        try:
            session_maker = self.app.session_maker()
            session = await session_maker.__aenter__()
        except Exception as err:
            msg_template = "Unexpected error handled: %r"
            logger.exception(msg_template, err)
            raise UnexpectedError(msg_template % (err,))

        try:
            self.request.state.db_session = session
            self.db_session = session

            await self._authenticate()
            await self._check_permissions()

            response = await handler(self.request)  # noqa
            await session.commit()

        except (BaseApplicationError, WebargsHTTPException, HTTPException) as err:
            await session.rollback()
            raise err

        except Exception as err:
            await session.rollback()
            msg_template = "Unexpected error handled: %r"
            logger.exception(msg_template, err)
            raise UnexpectedError(msg_template % (err,))

        finally:
            await session_maker.__aexit__(*sys.exc_info())
            self.request.state.db_session = None

        await response(self.scope, self.receive, self.send)

    async def _authenticate(self):
        if self.auth_backend:
            backend = self.auth_backend(self.request, self.scope)
            user = await backend.authenticate()
            self.scope["user"] = user
        else:
            self.scope["user"] = AnonymousUser()

    async def _check_permissions(self):
        for permission_class in self.permission_classes:
            try:
                has_permission = await permission_class().has_permission(self.request, self.scope)
                if not has_permission:
                    raise PermissionDeniedError
            # Exception may be raised inside permission_class, to pass additional details
            except PermissionDeniedError as exc:
                raise exc
            except Exception as exc:
                raise PermissionDeniedError from exc

    async def _validate(
        self, request, schema: Type[Schema] = None, partial_: bool = False, location: str = None
    ) -> Optional[Mapping]:
        """Simple validation, based on marshmallow's schemas"""

        schema_class = schema or self.request_schema
        schema_kwargs = {}
        if partial_:
            schema_kwargs["partial"] = [field for field in schema_class().fields]

        schema_obj, cleaned_data = schema_class(**schema_kwargs), {}
        try:
            cleaned_data = await self.request_parser().parse(schema_obj, request, location=location)
            if hasattr(schema_obj, "is_valid") and callable(schema_obj.is_valid):
                schema_obj.is_valid(cleaned_data)

        except ValidationError as e:
            # TODO: check that details is str / flatten
            raise InvalidParameterError(details=e.data)

        return cleaned_data

    def _response(
        self,
        data: Union[DBModel, Iterable[DBModel], dict] = None,
        status_code: int = status.HTTP_200_OK,
        response_status: ResponseStatus = ResponseStatus.OK,
        headers: Mapping[str, str] = None,
        background: Optional[BackgroundTasks] = None,
    ) -> BaseRenderer:
        """
        A shorthand for response_renderer plus serializing data and passing text status.
        To be used primarily with JSONRenderer and such.
        """
        if (data is not None) and self.response_schema:
            schema_kwargs = {}
            if isinstance(data, Iterable) and not isinstance(data, dict):
                schema_kwargs["many"] = True

            payload = self.response_schema(**schema_kwargs).dump(data)
        else:
            payload = data

        return self.response_renderer(
            self._get_response_content(response_status, payload),
            status_code=status_code,
            headers=headers,
            background=background,
        )

    @staticmethod
    def _get_response_content(response_status: ResponseStatus, payload: Any) -> Dict:
        return {"status": response_status, "payload": payload}
