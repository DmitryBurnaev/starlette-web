from starlette_web.common.utils import TextChoices


class ResponseStatus(TextChoices):
    # 2xx
    OK = "OK"
    CREATED = "CREATED"
    ACCEPTED = "ACCEPTED"
    NO_CONTENT = "NO_CONTENT"

    # 4xx
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    AUTH_FAILED = "AUTH_FAILED"
    MISSED_CREDENTIALS = "MISSED_CREDENTIALS"
    SIGNATURE_EXPIRED = "SIGNATURE_EXPIRED"
    INVITE_ERROR = "INVITE_ERROR"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    NOT_ALLOWED = "NOT_ALLOWED"
    NOT_ACCEPTABLE = "NOT_ACCEPTABLE"
    CONFLICT = "CONFLICT"
    I_AM_A_TEAPOT = "I_AM_A_TEAPOT"
    UNPROCESSABLE_ENTRY = "UNPROCESSABLE_ENTRY"

    # 5xx
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_COMMUNICATION_ERROR = "SERVICE_COMMUNICATION_ERROR"


def status_is_success(code: int) -> bool:
    return 200 <= code <= 299


def status_is_server_error(code: int) -> bool:
    return 500 <= code <= 600
