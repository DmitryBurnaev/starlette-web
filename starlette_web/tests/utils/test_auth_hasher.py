import uuid

from starlette_web.contrib.auth.hasher import PBKDF2PasswordHasher


def test_password_encode():
    hasher = PBKDF2PasswordHasher()
    row_password = uuid.uuid4().hex
    encoded = hasher.encode(row_password, salt="test_salt")
    algorithm, iterations, salt, hash_ = encoded.split("$", 3)
    assert salt == "test_salt"
    assert algorithm == "pbkdf2_sha256"
    assert hash_ != row_password


def test_password_verify__ok():
    hasher = PBKDF2PasswordHasher()
    row_password = uuid.uuid4().hex
    encoded = hasher.encode(row_password, salt="test_salt")
    assert hasher.verify(row_password, encoded) == (True, "")


def test_password_verify__incompatible_format__fail():
    hasher = PBKDF2PasswordHasher()
    verified, err_message = hasher.verify(uuid.uuid4().hex, "fake-encoded-password")
    assert not verified
    assert err_message == (
        "Encoded password has incompatible format: not enough values to unpack (expected 4, got 1)"
    )


def test_password_verify__algorithm_mismatch__fail():
    hasher = PBKDF2PasswordHasher()
    verified, err_message = hasher.verify(uuid.uuid4().hex, "fake-algorithm$1000$salt$enc-password")
    assert not verified
    assert err_message == "Algorithm mismatch!: fake-algorithm != pbkdf2_sha256"
