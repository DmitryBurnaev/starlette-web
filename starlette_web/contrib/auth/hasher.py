import base64
import hashlib
import hmac
import secrets
import string
import uuid
from typing import Tuple

from starlette_web.common.utils import get_logger

logger = get_logger(__name__)


def get_salt(length=12) -> str:
    """Returns a securely generated random string."""

    allowed_chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(allowed_chars) for _ in range(length))


def get_random_hash(size: int) -> str:
    """Allows calculating random hash with fixed length"""

    h = hashlib.blake2b(key=get_salt().encode(), digest_size=size)
    h.update(str(uuid.uuid4()).encode())
    return h.hexdigest()[:size]


class PBKDF2PasswordHasher:
    """
    Secure password hashing using the PBKDF2 algorithm (recommended)

    Configured to use PBKDF2 + HMAC + SHA256.
    The result is a 64 byte binary string.  Iterations may be changed
    safely, but you must rename the algorithm if you change SHA256.
    """

    algorithm = "pbkdf2_sha256"
    iterations = 180000
    digest = hashlib.sha256

    def encode(self, password: str, salt: str = None) -> str:
        """Encoding password using random salt + pbkdf2_sha256"""
        salt = salt or get_salt()
        assert password is not None
        assert salt and "$" not in salt
        hash_ = self._pbkdf2(password, salt)
        hash_ = base64.b64encode(hash_).decode("ascii").strip()
        return "%s$%d$%s$%s" % (self.algorithm, self.iterations, salt, hash_)

    def verify(self, password: str, encoded: str) -> Tuple[bool, str]:
        """Check if the given password is correct."""
        try:
            algorithm, iterations, salt, _ = encoded.split("$", 3)
        except ValueError as err:
            err_message = f"Encoded password has incompatible format: {err}"
            logger.warning(err_message)
            return False, err_message

        if algorithm != self.algorithm:
            err_message = f"Algorithm mismatch!: {algorithm} != {self.algorithm}"
            logger.warning(err_message)
            return False, err_message

        encoded_2 = self.encode(password, salt)
        return hmac.compare_digest(encoded, encoded_2), ""

    def _pbkdf2(self, password: str, salt: str) -> bytes:
        """Return the hash of password using pbkdf2."""
        digest = self.digest
        iterations = self.iterations
        password = bytes(password, encoding="utf-8")
        salt = bytes(salt, encoding="utf-8")
        return hashlib.pbkdf2_hmac(digest().name, password, salt, iterations)
