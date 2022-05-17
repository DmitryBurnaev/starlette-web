# Copy from https://github.com/django/django/blob/main/django/utils/crypto.py

import secrets
import string
from typing import Union


RANDOM_STRING_CHARS = string.ascii_letters + string.digits


def _force_bytes(value: Union[str, bytes], encoding="utf-8", errors="strict"):
    if isinstance(value, bytes):
        if encoding == "utf-8":
            return value
        else:
            return value.decode("utf-8", errors).encode(encoding, errors)
    if isinstance(value, memoryview):
        return bytes(value)
    return str(value).encode(encoding, errors)


def get_random_string(length, allowed_chars=RANDOM_STRING_CHARS):
    """
    Return a securely generated random string.
    The bit length of the returned value can be calculated with the formula:
        log_2(len(allowed_chars)^length)
    For example, with default `allowed_chars` (26+26+10), this gives:
      * length: 12, bit length =~ 71 bits
      * length: 22, bit length =~ 131 bits
    """
    return "".join([secrets.choice(allowed_chars) for _ in range(length)])


def constant_time_compare(val1, val2):
    """Return True if the two strings are equal, False otherwise."""
    return secrets.compare_digest(_force_bytes(val1), _force_bytes(val2))
