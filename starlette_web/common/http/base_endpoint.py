from typing import Type, Union, Iterable, ClassVar, Optional, Mapping, List

from marshmallow import Schema, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.background import BackgroundTasks
from starlette.exceptions import HTTPException
from starlette.endpoints import HTTPEndpoint
from webargs_starlette import WebargsHTTPException, StarletteParser

from starlette_web.common.authorization.backends import (
    BaseAuthenticationBackend,
    NoAuthenticationBackend,
)
from starlette_web.common.authorization.permissions import BasePermission, OperandHolder
from starlette_web.common.authorization.base_user import AnonymousUser
from starlette_web.common.http.exceptions import (
    UnexpectedError,
    BaseApplicationError,
    InvalidParameterError,
    PermissionDeniedError,
)
from starlette_web.common.http.renderers import BaseRenderer, JSONRenderer
from starlette_web.common.http.requests import PRequest
from starlette_web.common.http.statuses import ResponseStatus
from starlette_web.common.database import DBModel
from starlette_web.common.utils import get_logger


logger = get_logger(__name__)


class BaseHTTPEndpoint(HTTPEndpoint):
    """
    Base View witch used as a base class for every API's endpoints
    """

    app = None
    request: PRequest
    db_model: ClassVar[DBModel]
    db_session: AsyncSession
    schema_request: ClassVar[Type[Schema]]
    schema_response: ClassVar[Type[Schema]]
    auth_backend: Type[BaseAuthenticationBackend] = NoAuthenticationBackend
    permission_classes: List[Union[Type[BasePermission], OperandHolder]] = []
    request_parser: Type[StarletteParser] = StarletteParser
    response_renderer: Type[BaseRenderer] = JSONRenderer

    async def dispatch(self) -> None:
        """
        This method is calling in every request.
        So, we can use this one for customs authenticate and catch all exceptions
        """

        self.request = PRequest(self.scope, receive=self.receive)
        self.app = self.scope.get("app")

        handler_name = "get" if self.request.method == "HEAD" else self.request.method.lower()
        handler = getattr(self, handler_name, self.method_not_allowed)

        try:
            async with self.app.session_maker() as session:
                self.request.db_session = session
                self.db_session = session

                await self._authenticate()
                await self._check_permissions()

                response = await handler(self.request)  # noqa
                await self.db_session.commit()

        except (BaseApplicationError, WebargsHTTPException, HTTPException) as err:
            await self.db_session.rollback()
            raise err

        except Exception as err:
            await self.db_session.rollback()
            msg_template = "Unexpected error handled: %r"
            logger.exception(msg_template, err)
            raise UnexpectedError(msg_template % (err,))

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

        schema_request = schema or self.schema_request
        schema_kwargs = {}
        if partial_:
            schema_kwargs["partial"] = [field for field in schema_request().fields]

        schema, cleaned_data = schema_request(**schema_kwargs), {}
        try:
            cleaned_data = await self.request_parser().parse(schema, request, location=location)
            if hasattr(schema, "is_valid") and callable(schema.is_valid):
                schema.is_valid(cleaned_data)

        except ValidationError as e:
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
        if (data is not None) and self.schema_response:
            schema_kwargs = {}
            if isinstance(data, Iterable) and not isinstance(data, dict):
                schema_kwargs["many"] = True

            payload = self.schema_response(**schema_kwargs).dump(data)
        else:
            payload = data

        # TODO: Pass only payload to renderer? Maybe pass string-like response_status independently?
        return self.response_renderer(
            {"status": response_status, "payload": payload},
            status_code=status_code,
            headers=headers,
            background=background,
        )
