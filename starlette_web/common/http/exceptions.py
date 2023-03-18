from starlette_web.common.http.statuses import ResponseStatus


class BaseApplicationError(Exception):
    message = "Something went wrong"
    details = None
    status_code = 500
    response_status = ResponseStatus.INTERNAL_ERROR

    def __init__(
        self,
        details: str = None,
        message: str = None,
        status_code: int = None,
        response_status: str = None,
    ):
        self.message = message or self.message
        self.details = details or self.details
        self.status_code = status_code or self.status_code
        self.response_status = response_status or self.response_status

    def __str__(self):
        return f"{self.message}\n{self.details}".strip()

    def __iter__(self):
        yield "message", self.message
        yield "details", self.details
        yield "status_code", self.status_code
        yield "response_status", self.response_status


class ImproperlyConfigured(BaseApplicationError):
    message = "Application is configured improperly."


class UnexpectedError(BaseApplicationError):
    message = "Something unexpected happened."


class NotSupportedError(BaseApplicationError):
    message = "Requested action is not supported now"


class HttpError(BaseApplicationError):
    message = "Some HTTP error happened."


class InvalidParameterError(BaseApplicationError):
    status_code = 400
    message = "Requested data is not valid."
    response_status = ResponseStatus.INVALID_PARAMETERS


class AuthenticationFailedError(BaseApplicationError):
    status_code = 401
    response_status = ResponseStatus.AUTH_FAILED
    message = "Authentication credentials are invalid."


class AuthenticationRequiredError(AuthenticationFailedError):
    status_code = 401
    response_status = ResponseStatus.MISSED_CREDENTIALS
    message = "Authentication is required."


class SignatureExpiredError(AuthenticationFailedError):
    status_code = 401
    response_status = ResponseStatus.SIGNATURE_EXPIRED
    message = "Authentication credentials are invalid."


class InviteTokenInvalidationError(BaseApplicationError):
    status_code = 401
    message = "Requested token is expired or does not exist."
    response_status = ResponseStatus.INVITE_ERROR


class PermissionDeniedError(BaseApplicationError):
    status_code = 403
    message = "You don't have permission to perform this action."
    response_status = ResponseStatus.FORBIDDEN


class NotFoundError(BaseApplicationError):
    status_code = 404
    message = "Requested object not found."
    response_status = ResponseStatus.NOT_FOUND


class MethodNotAllowedError(BaseApplicationError):
    status_code = 405
    message = "Requested method is not allowed."
    response_status = ResponseStatus.NOT_ALLOWED


class NotAcceptableError(BaseApplicationError):
    status_code = 406
    message = (
        "Request cannot be processed, "
        "Accept-* headers are incompatible with server."
    )
    response_status = ResponseStatus.NOT_ALLOWED


class ConflictError(BaseApplicationError):
    status_code = 409
    message = "Request conflicts with current state of server."
    response_status = ResponseStatus.CONFLICT


class ImATeapotError(BaseApplicationError):
    status_code = 418
    message = "The server cannot brew a coffee, because it is a teapot."
    response_status = ResponseStatus.I_AM_A_TEAPOT


class UnprocessableEntryError(BaseApplicationError):
    status_code = 422
    message = "Could not process request due to logical errors in data."
    response_status = ResponseStatus.UNPROCESSABLE_ENTRY


class InvalidResponseError(BaseApplicationError):
    status_code = 500
    message = "Response data couldn't be serialized."


class NotImplementedByServerError(BaseApplicationError):
    status_code = 501
    message = "Functionality is not supported by the server."


class SendRequestError(BaseApplicationError):
    status_code = 503
    message = "Got unexpected error for sending request."
    response_status = ResponseStatus.SERVICE_COMMUNICATION_ERROR


class MaxAttemptsReached(BaseApplicationError):
    status_code = 503
    message = "Reached max attempt to make action"
