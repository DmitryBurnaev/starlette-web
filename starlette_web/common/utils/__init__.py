import logging
import logging.config
from importlib import import_module
from typing import Type

import httpx
from starlette import status
from starlette.responses import JSONResponse
from webargs_starlette import WebargsHTTPException

from starlette_web.core import settings
from starlette_web.common.http.statuses import ResponseStatus
from starlette_web.common.http.exceptions import BaseApplicationError, SendRequestError


# TODO: refactor the file
def get_logger(name: str = None):
    """Getting configured logger"""
    return logging.getLogger(name or "app")


# TODO: move to common.http
def status_is_success(code):
    return 200 <= code <= 299


def status_is_server_error(code):
    return 500 <= code <= 600


def log_message(exc, error_data, level=logging.ERROR):
    """
    Helps to log caught errors by exception handler
    """
    logger = get_logger(__name__)

    error_details = {
        "error": error_data.get("error", "Unbound exception"),
        "details": error_data.get("details", str(exc)),
    }
    message = "{exc.__class__.__name__} '{error}': [{details}]".format(exc=exc, **error_details)
    logger.log(level, message, exc_info=(level == logging.ERROR))


# TODO: move to common.http
# TODO: use JSONRenderer
def custom_exception_handler(request, exc):
    """
    Returns the response that should be used for any given exception.
    Response will be formatted by our format: {"error": "text", "detail": details}
    """
    error_message = "Something went wrong!"
    error_details = f"Raised Error: {exc.__class__.__name__}"
    status_code = getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
    response_status = ResponseStatus.INTERNAL_ERROR
    if isinstance(exc, BaseApplicationError):
        error_message = exc.message
        error_details = exc.details
        response_status = exc.response_status

    elif isinstance(exc, WebargsHTTPException):
        error_message = "Requested data is not valid."
        error_details = exc.messages.get("json") or exc.messages.get("form") or exc.messages
        status_code = status.HTTP_400_BAD_REQUEST
        response_status = ResponseStatus.INVALID_PARAMETERS

    payload = {"error": error_message}
    if settings.APP_DEBUG or response_status == ResponseStatus.INVALID_PARAMETERS:
        payload["details"] = error_details

    response_data = {"status": response_status, "payload": payload}
    log_level = logging.ERROR if status_is_server_error(status_code) else logging.WARNING
    log_message(exc, response_data["payload"], log_level)
    return JSONResponse(response_data, status_code=status_code)


async def send_email(recipient_email: str, subject: str, html_content: str):
    """Allows sending email via Sendgrid API"""

    request_url = f"https://api.sendgrid.com/{settings.SENDGRID_API_VERSION}/mail/send"
    request_data = {
        "personalizations": [{"to": [{"email": recipient_email}], "subject": subject}],
        "from": {"email": settings.EMAIL_FROM},
        "content": [{"type": "text/html", "value": html_content}],
    }
    request_header = {"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"}
    request_logger = get_logger(__name__)
    request_logger.info("Send request to %s. Data: %s", request_url, request_data)

    async with httpx.AsyncClient() as client:
        response = await client.post(request_url, json=request_data, headers=request_header)
        status_code = response.status_code
        if not status_is_success(status_code):
            response_text = response.json()
            raise SendRequestError(
                message=f"Couldn't send email to {recipient_email}",
                details=f"Got status code: {status_code}; response text: {response_text}",
                request_url=request_url,
            )
        else:
            request_logger.info("Email sent to %s. Status code: %s", recipient_email, status_code)


def cut_string(source_string: str, max_length: int, finish_seq: str = "...") -> str:
    """
    Allows limiting source_string and append required sequence

    >>> cut_string('Some long string', max_length=13)
    'Some long ...'
    >>> cut_string('Some long string', max_length=8, finish_seq="***")
    'Some ***'
    >>> cut_string('Some long string', max_length=1)
    ''
    """
    if len(source_string) > max_length:
        slice_length = max_length - len(finish_seq)
        return source_string[:slice_length] + finish_seq if (slice_length > 0) else ""

    return source_string


def import_string(dotted_path) -> Type[object]:
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % dotted_path) from err

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        error_description = 'Module "%s" does not define a "%s" attribute/class' % (
            module_path,
            class_name,
        )
        raise ImportError(error_description) from err
