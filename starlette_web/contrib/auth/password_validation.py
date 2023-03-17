from difflib import SequenceMatcher
from functools import cache
from typing import Optional

from starlette_web.common.conf import settings
from starlette_web.common.http.exceptions import NotSupportedError, InvalidParameterError
from starlette_web.common.utils.importing import import_string
from starlette_web.contrib.auth.models import User


# TODO: maybe raise marshmallow.ValidationError ?
# TODO: add common password validators
class BasePasswordValidator:
    def __init__(self, **options):
        self.options = options

    def __call__(self, password: str, user: Optional[User] = None):
        raise NotSupportedError()


class PasswordLengthValidator(BasePasswordValidator):
    def __init__(self, **options):
        super().__init__(**options)
        self.min_length = options.get("MIN_LENGTH", 8)
        if type(self.min_length) != int or self.min_length < 0:
            raise NotSupportedError(details="Invalid input options for MIN_LENGTH.")
        self.max_length = options.get("MAX_LENGTH", 64)
        if type(self.max_length) != int or self.max_length < 0:
            raise NotSupportedError(details="Invalid input options for MAX_LENGTH.")

    def __call__(self, password: str, user: Optional[User] = None):
        if len(password) < self.min_length:
            raise InvalidParameterError(details=f"Password length is less than {self.min_length}.")

        if len(password) > self.max_length:
            raise InvalidParameterError(details=f"Password length is more than {self.max_length}.")


class UsernameSimilarityValidator(BasePasswordValidator):
    def __init__(self, **options):
        super().__init__(**options)
        self.max_similarity = options.get("MAX_SIMILARITY", 0.7)
        if type(self.max_similarity) != float or not (0 <= self.max_similarity <= 1):
            raise NotSupportedError(details="Invalid input options for MAX_SIMILARITY.")

    def __call__(self, password: str, user: Optional[User] = None):
        if not user:
            return

        if (
            SequenceMatcher(
                a=password.lower(),
                b=user.email.lower(),
            ).quick_ratio()
            > self.max_similarity
        ):
            raise InvalidParameterError(details="Password is too similar with username.")


class NumericPasswordValidator(BasePasswordValidator):
    def __call__(self, password: str, user: Optional[User] = None):
        if password.isdigit():
            raise InvalidParameterError(details="Password is entirely numeric.")


@cache
def _get_validators():
    validators = []
    for validator_setting in settings.PASSWORD_VALIDATORS:
        validator_class = import_string(validator_setting["BACKEND"])
        options = validator_setting.get("OPTIONS", {})
        validators.append(validator_class(**options))
    return validators


def validate_password(password, user: Optional[User] = None):
    for validator in _get_validators():
        validator(password, user)
