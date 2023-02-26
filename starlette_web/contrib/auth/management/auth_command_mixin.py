from marshmallow.validate import ValidationError, Email as EmailValidator

from starlette_web.common.management.base import CommandError


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
