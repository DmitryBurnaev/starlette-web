import logging
from starlette import status
from marshmallow import Schema, fields

from starlette_web.contrib.auth.models import User
from starlette_web.common.http.base_endpoint import BaseHTTPEndpoint
from starlette_web.common.http.exceptions import BaseApplicationError
from starlette_web.common.http.statuses import ResponseStatus


logger = logging.getLogger(__name__)


class ServicesCheckSchema(Schema):
    postgres = fields.Str()


class HealthCheckSchema(Schema):
    services = fields.Nested(ServicesCheckSchema)
    errors = fields.List(fields.Str)


class HealthCheckAPIView(BaseHTTPEndpoint):
    """Allows controlling status of web application (live ASGI and pg connection)"""

    auth_backend = None
    schema_response = HealthCheckSchema

    async def get(self, *_):
        """
        description: Health check of services
        responses:
          200:
            description: Services with status
            content:
              application/json:
                schema: HealthCheckSchema
          503:
            description: Service unavailable
        tags: ["Health check"]
        """
        response_data = {"services": {}, "errors": []}
        result_status = status.HTTP_200_OK
        response_status = ResponseStatus.OK

        try:
            await User.async_filter(self.db_session)
        except Exception as error:
            error_msg = f"Couldn't connect to DB: {error.__class__.__name__} '{error}'"
            logger.exception(error_msg)
            response_data["services"]["postgres"] = "down"
            response_data["errors"].append(error_msg)
        else:
            response_data["services"]["postgres"] = "ok"

        services = response_data.get("services").values()

        if "down" in services or response_data.get("errors"):
            response_data["status"] = "down"
            result_status = status.HTTP_503_SERVICE_UNAVAILABLE
            response_status = ResponseStatus.INTERNAL_ERROR

        return self._response(
            data=response_data, status_code=result_status, response_status=response_status
        )


class SentryCheckAPIView(BaseHTTPEndpoint):
    """Simple checker sentry config (raise err + logger)."""

    auth_backend = None

    async def get(self, request):  # noqa
        """
        description: Health check of Sentry logger
        responses:
          500:
            description: Application error
        tags: ["Health check"]
        """
        logger.error("Error check sentry")
        try:
            1 / 0
        except ZeroDivisionError as err:
            logger.exception(f"Test exc for sentry: {err}")

        raise BaseApplicationError("Oops!")
