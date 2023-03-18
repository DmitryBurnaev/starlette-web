from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Tuple

import jwt

from starlette_web.common.conf import settings


TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"
TOKEN_TYPE_RESET_PASSWORD = "reset_password"


@dataclass
class TokenCollection:
    refresh_token: str
    refresh_token_expired_at: datetime
    access_token: str
    access_token_expired_at: datetime


def encode_jwt(
    payload: dict,
    token_type: str = TOKEN_TYPE_ACCESS,
    expires_in: int = None,
) -> Tuple[str, datetime]:
    """Allows to prepare JWT for auth engine"""

    if token_type == TOKEN_TYPE_REFRESH:
        expires_in = settings.AUTH_JWT_REFRESH_EXPIRES_IN
    else:
        expires_in = expires_in or settings.AUTH_JWT_EXPIRES_IN

    expired_at = datetime.utcnow() + timedelta(seconds=expires_in)
    payload["exp"] = expired_at
    payload["exp_iso"] = expired_at.isoformat()
    payload["token_type"] = token_type
    token = jwt.encode(
        payload,
        str(settings.SECRET_KEY),
        algorithm=settings.AUTH_JWT_ALGORITHM,
    )
    return token, expired_at


def decode_jwt(encoded_jwt: str) -> dict:
    """Allows to decode received JWT token to payload"""

    return jwt.decode(
        encoded_jwt,
        str(settings.SECRET_KEY),
        algorithms=[settings.AUTH_JWT_ALGORITHM],
    )
