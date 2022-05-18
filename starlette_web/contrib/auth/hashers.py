import base64
import hashlib
import math
from typing import Optional, Dict, Union

from starlette_web.common.exceptions import ImproperlyConfigured
from starlette_web.common.utils.importing import import_string
from starlette_web.common.utils.singleton import Singleton
from starlette_web.common.utils.crypto import (
    get_random_string,
    constant_time_compare,
    RANDOM_STRING_CHARS,
)
from starlette_web.core import settings


class BasePasswordHasher(metaclass=Singleton):
    algorithm = None
    salt_entropy = 128

    def salt(self) -> str:
        char_count = math.ceil(self.salt_entropy / math.log2(len(RANDOM_STRING_CHARS)))
        return get_random_string(char_count, allowed_chars=RANDOM_STRING_CHARS)

    def encode(self, password: str, salt: Optional[str] = None) -> str:
        raise NotImplementedError

    def verify(self, password: str, encoded: str) -> bool:
        """Check if the given password is correct."""
        try:
            algorithm, iterations, salt, _ = encoded.split("$", 3)
        except ValueError:
            return False

        if algorithm != self.algorithm:
            return False

        encoded_2 = self.encode(password, salt)
        return constant_time_compare(encoded, encoded_2)


class PBKDF2PasswordHasher(BasePasswordHasher):
    """
    Secure password hashing using the PBKDF2 algorithm (recommended)

    Configured to use PBKDF2 + HMAC + SHA256.
    The result is a 64 byte binary string. Iterations may be changed
    safely, but you must rename the algorithm if you change SHA256.
    """

    algorithm = "pbkdf2_sha256"
    iterations = 180000
    digest = hashlib.sha256

    def encode(self, password: str, salt: str = None) -> str:
        """Encoding password using random salt + pbkdf2_sha256"""
        salt = salt or self.salt()
        assert password is not None
        assert salt and "$" not in salt
        hash_ = self._pbkdf2(password, salt)
        hash_ = base64.b64encode(hash_).decode("ascii").strip()
        return "%s$%d$%s$%s" % (self.algorithm, self.iterations, salt, hash_)

    def _pbkdf2(self, password: str, salt: str) -> bytes:
        """Return the hash of password using pbkdf2."""
        digest = self.digest
        iterations = self.iterations
        password = bytes(password, encoding="utf-8")
        salt = bytes(salt, encoding="utf-8")
        return hashlib.pbkdf2_hmac(digest().name, password, salt, iterations)


class PasswordManager(metaclass=Singleton):
    def __init__(self):
        self._password_hashers: Dict[str, BasePasswordHasher] = dict()
        for password_hasher in settings.PASSWORD_HASHERS:
            self._add_password_hasher(password_hasher)

    def _add_password_hasher(self, hasher: Union[str, BasePasswordHasher]) -> None:
        if type(hasher) == str:
            self._password_hashers[hasher] = import_string(hasher)()
        else:
            self._password_hashers[hasher.__class__.__name__] = hasher

    def verify_password(self, password: str, encoded: str) -> bool:
        return any(
            (
                self._password_hashers[hasher].verify(password, encoded)
                for hasher in self._password_hashers.keys()
            )
        )

    def make_password(self, password: str, salt: Optional[str] = None) -> str:
        try:
            hasher = settings.PASSWORD_HASHERS[0]
        except IndexError:
            raise ImproperlyConfigured(
                'At least 1 password hasher must be defined at settings.PASSWORD_HASHERS'
            )

        return self._password_hashers[hasher].encode(password, salt)

    def get_hashers(self) -> Dict[str, BasePasswordHasher]:
        return self._password_hashers


_password_manager = PasswordManager()
make_password = _password_manager.make_password
verify_password = _password_manager.verify_password
