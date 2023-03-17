from marshmallow.validate import ValidationError, Email as EmailValidator

from starlette_web.common.http.exceptions import InvalidParameterError
from starlette_web.common.management.base import CommandError
from starlette_web.contrib.auth.password_validation import validate_password as _validate_password


class AuthCommandMixin:
    # TODO: Support masking for passwords ?
    def get_input_data(self, message, default=None):
        raw_value = input(message)
        if default and raw_value == "":
            raw_value = default
        return raw_value

    def validate_field(self, field_name: str, value: str):
        if not value:
            raise CommandError(details="Field value is empty.")

        if field_name == "email":
            try:
                EmailValidator()(value)
            except ValidationError:
                raise CommandError(details="Invalid value for email.")

    def validate_password(self, password, user=None):
        try:
            _validate_password(password, user=user)
        except InvalidParameterError as exc:
            print(f"Weak password: {exc.details}")
            answer = input("Skip validation and continue? (y/n): ")

            if answer.strip() not in ["y", "Y", "yes"]:
                raise exc
