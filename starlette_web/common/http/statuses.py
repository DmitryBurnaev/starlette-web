from starlette_web.common.utils import TextChoices


class ResponseStatus(TextChoices):
    OK = "OK"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    AUTH_FAILED = "AUTH_FAILED"
    MISSED_CREDENTIALS = "MISSED_CREDENTIALS"
    SIGNATURE_EXPIRED = "SIGNATURE_EXPIRED"
    NOT_FOUND = "NOT_FOUND"
    NOT_ALLOWED = "NOT_ALLOWED"
    INVITE_ERROR = "INVITE_ERROR"
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    FORBIDDEN = "FORBIDDEN"
    SERVICE_COMMUNICATION_ERROR = "SERVICE_COMMUNICATION_ERROR"


def status_is_success(code: int) -> bool:
    return 200 <= code <= 299


def status_is_server_error(code: int) -> bool:
    return 500 <= code <= 600
