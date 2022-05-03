import logging
import logging.config

from starlette import status
from webargs_starlette import WebargsHTTPException

from starlette_web.core import settings
from starlette_web.common.http.requests import PRequest
from starlette_web.common.http.renderers import BaseRenderer, JSONRenderer
from starlette_web.common.http.statuses import ResponseStatus, status_is_server_error
from starlette_web.common.http.exceptions import BaseApplicationError
from starlette_web.common.utils import log_message


class BaseExceptionHandler:
    def _get_error_message(self, request: PRequest, exc: Exception):
        return "Something went wrong!"

    def _get_error_details(self, request: PRequest, exc: Exception):
        return f"Raised Error: {exc.__class__.__name__}"

    def _get_status_code(self, request: PRequest, exc: Exception):
        return getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_response_status(self, request: PRequest, exc: Exception):
        return ResponseStatus.INTERNAL_ERROR

    def __call__(self, request: PRequest, exc: Exception) -> BaseRenderer:
        error_message = self._get_error_message(request, exc)
        error_details = self._get_error_details(request, exc)
        status_code = self._get_status_code(request, exc)
        response_status = self._get_response_status(request, exc)

        payload = {"error": error_message}
        if settings.APP_DEBUG or response_status == ResponseStatus.INVALID_PARAMETERS:
            payload["details"] = error_details

        response_data = {"status": response_status, "payload": payload}
        log_level = logging.ERROR if status_is_server_error(status_code) else logging.WARNING
        log_message(exc, response_data["payload"], log_level)
        return JSONRenderer(response_data, status_code=status_code)


class BaseApplicationErrorHandler(BaseExceptionHandler):
    def _get_error_details(self, request: PRequest, exc: BaseApplicationError):
        return exc.details

    def _get_error_message(self, request: PRequest, exc: BaseApplicationError):
        return exc.message

    def _get_response_status(self, request: PRequest, exc: BaseApplicationError):
        return exc.response_status


class WebargsHTTPExceptionHandler(BaseExceptionHandler):
    def _get_error_details(self, request: PRequest, exc: WebargsHTTPException):
        return exc.messages.get("json") or exc.messages.get("form") or exc.messages

    def _get_error_message(self, request: PRequest, exc: WebargsHTTPException):
        return "Requested data is not valid."

    def _get_response_status(self, request: PRequest, exc: WebargsHTTPException):
        return ResponseStatus.INVALID_PARAMETERS

    def _get_status_code(self, request: PRequest, exc: Exception):
        return status.HTTP_400_BAD_REQUEST
