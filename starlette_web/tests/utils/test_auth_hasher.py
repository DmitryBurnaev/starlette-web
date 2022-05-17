import hashlib
import uuid

from starlette_web.contrib.auth.hashers import (
    PBKDF2PasswordHasher,
    make_password,
    verify_password,
    _password_manager,
    BasePasswordHasher,
)


class MD5PasswordHasher(BasePasswordHasher):
    """
    The Salted MD5 password hashing algorithm (not recommended)
    """

    algorithm = "md5"

    def encode(self, password, salt=None) -> str:
        assert password is not None
        assert salt and "$" not in salt
        hash = hashlib.md5((salt + password).encode()).hexdigest()
        return "%s$1$%s$%s" % (self.algorithm, salt, hash)


def test_password_encode():
    hasher = PBKDF2PasswordHasher()
    raw_password = uuid.uuid4().hex
    encoded = hasher.encode(raw_password, salt="test_salt")
    algorithm, iterations, salt, hash_ = encoded.split("$", 3)
    assert salt == "test_salt"
    assert algorithm == "pbkdf2_sha256"
    assert hash_ != raw_password


def test_password_verify__ok():
    hasher = PBKDF2PasswordHasher()
    raw_password = uuid.uuid4().hex
    encoded = hasher.encode(raw_password, salt="test_salt")
    verified = hasher.verify(raw_password, encoded)
    assert verified


def test_password_verify__incompatible_format__fail():
    hasher = PBKDF2PasswordHasher()
    verified = hasher.verify(uuid.uuid4().hex, "fake-encoded-password")
    assert not verified


def test_password_verify__algorithm_mismatch__fail():
    hasher = PBKDF2PasswordHasher()
    verified = hasher.verify(uuid.uuid4().hex, "fake-algorithm$1000$salt$enc-password")
    assert not verified


def test_generic_hasher_utils():
    hasher = PBKDF2PasswordHasher()
    raw_password = uuid.uuid4().hex
    salt = hasher.salt()

    password_1 = hasher.encode(raw_password, salt)
    password_2 = make_password(raw_password, salt)
    assert password_1 == password_2
    assert verify_password(raw_password, password_1)


def test_additional_hasher():
    _password_manager._add_password_hasher(MD5PasswordHasher())
    raw_password = uuid.uuid4().hex
    salt = uuid.uuid4().hex

    # Python 3.7+ guarantees order of keys, so PBKDF2PasswordHasher is always first
    # as long as it is first in settings.PASSWORD_HASHERS
    # https://mail.python.org/pipermail/python-dev/2017-December/151283.html
    encoded_password = make_password(raw_password, salt)
    pdkdf2_password = PBKDF2PasswordHasher().encode(raw_password, salt)
    assert encoded_password == pdkdf2_password

    assert PBKDF2PasswordHasher().verify(raw_password, encoded_password)
    assert verify_password(raw_password, encoded_password)
