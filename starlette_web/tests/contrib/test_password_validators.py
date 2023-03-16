import pytest

from starlette_web.common.http.exceptions import InvalidParameterError
from starlette_web.contrib.auth.models import User
from starlette_web.contrib.auth.password_validation import password_validators, validate_password


def test_password_validation():
    assert len(password_validators) == 3

    with pytest.raises(InvalidParameterError) as exc:
        validate_password("123456789")
    assert exc.value.details == "Password is entirely numeric."

    with pytest.raises(InvalidParameterError) as exc:
        validate_password("am6Yab8")
    assert exc.value.details == "Password length is less than 8."

    with pytest.raises(InvalidParameterError) as exc:
        _user = User(email="shocking.blue@gmail.com")
        validate_password("shocking.blue", _user)
    assert exc.value.details == "Password is too similar with username."

    validate_password("8IavAD9B5b81ifWU3K7G")
    validate_password("TfOqTEiDC2EezY8czZEE")
    validate_password("3pHYO6uPFkffkNN9BlPG")
