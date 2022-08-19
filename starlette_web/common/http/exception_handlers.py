import logging
import logging.config
from typing import Any, Optional

from starlette import status
from starlette.responses import BackgroundTask
from webargs_starlette import WebargsHTTPException

from starlette_web.common.conf import settings
from starlette_web.common.http.requests import PRequest
from starlette_web.common.http.renderers import BaseRenderer, JSONRenderer
from starlette_web.common.http.statuses import ResponseStatus, status_is_server_error
from starlette_web.common.http.exceptions import BaseApplicationError


class BaseExceptionHandler:
    renderer_class: BaseRenderer = JSONRenderer

    def _log_message(self, exc: Exception, error_data: dict, level=logging.ERROR):
        logger = logging.getLogger(__name__)

        error_details = {
            "error": error_data.get("error", "Unbound exception"),
            "details": error_data.get("details", str(exc)),
        }
        message = "{exc.__class__.__name__} '{error}': [{details}]".format(exc=exc, **error_details)
        logger.log(level, message, exc_info=(level == logging.ERROR))

    def _get_error_message(self, request: PRequest, exc: Exception) -> str:
        return "Something went wrong!"

    def _get_error_details(self, request: PRequest, exc: Exception) -> str:
        return f"Raised Error: {exc.__class__.__name__}"

    def _get_status_code(self, request: PRequest, exc: Exception) -> int:
        return getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_response_status(self, request: PRequest, exc: Exception) -> str:
        return ResponseStatus.INTERNAL_ERROR

    def _get_response_data(self, request: PRequest, exc: Exception) -> Any:
        error_message = self._get_error_message(request, exc)
        error_details = self._get_error_details(request, exc)
        response_status = self._get_response_status(request, exc)

        payload = {"error": error_message}
        if settings.APP_DEBUG or response_status == ResponseStatus.INVALID_PARAMETERS:
            payload["details"] = error_details

        return {"status": response_status, "payload": payload}

    def _on_error_action(self, request: PRequest, exc: Exception):
        status_code = self._get_status_code(request, exc)
        error_message = self._get_error_message(request, exc)
        payload = {"error": error_message}

        log_level = logging.ERROR if status_is_server_error(status_code) else logging.WARNING
        self._log_message(exc, payload, log_level)

    def _get_headers(self, request: PRequest, exc: Exception) -> Optional[dict]:
        return None

    def _get_background_tasks(self, request: PRequest, exc: Exception) -> Optional[BackgroundTask]:
        return None

    def __call__(self, request: PRequest, exc: Exception) -> BaseRenderer:
        self._on_error_action(request, exc)

        return self.renderer_class(
            content=self._get_response_data(request, exc),
            status_code=self._get_status_code(request, exc),
            background=self._get_background_tasks(request, exc),
            headers=self._get_headers(request, exc),
        )


class BaseApplicationErrorHandler(BaseExceptionHandler):
    def _get_error_details(self, request: PRequest, exc: BaseApplicationError) -> str:
        return exc.details

    def _get_error_message(self, request: PRequest, exc: BaseApplicationError) -> str:
        return exc.message

    def _get_response_status(self, request: PRequest, exc: BaseApplicationError) -> str:
        return exc.response_status


class WebargsHTTPExceptionHandler(BaseExceptionHandler):
    def _get_error_details(self, request: PRequest, exc: WebargsHTTPException):
        return exc.messages.get("json") or exc.messages.get("form") or exc.messages

    def _get_error_message(self, request: PRequest, exc: WebargsHTTPException) -> str:
        return "Requested data is not valid."

    def _get_response_status(self, request: PRequest, exc: WebargsHTTPException) -> str:
        return ResponseStatus.INVALID_PARAMETERS

    def _get_status_code(self, request: PRequest, exc: Exception) -> int:
        return status.HTTP_400_BAD_REQUEST
