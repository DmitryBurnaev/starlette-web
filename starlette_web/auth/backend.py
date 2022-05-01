from typing import Tuple

from jwt import InvalidTokenError, ExpiredSignatureError

from starlette_web.auth.models import User, UserSession
from starlette_web.auth.utils import decode_jwt, TOKEN_TYPE_ACCESS
from starlette_web.common.authorization.backends import BaseAuthenticationBackend
from starlette_web.common.http.exceptions import (
    AuthenticationFailedError,
    AuthenticationRequiredError,
    SignatureExpiredError,
)
from starlette_web.common.utils import get_logger

logger = get_logger(__name__)


class JWTAuthenticationBackend(BaseAuthenticationBackend):
    """Core of authenticate system, based on JWT auth approach"""

    keyword = "Bearer"

    async def authenticate(self) -> User:
        request = self.request

        auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
        if not auth_header:
            raise AuthenticationRequiredError("Invalid token header. No credentials provided.")

        auth = auth_header.split()
        if len(auth) != 2:
            logger.warning("Trying to authenticate with header %s", auth_header)
            raise AuthenticationFailedError("Invalid token header. Token should be format as JWT.")

        if auth[0] != self.keyword:
            raise AuthenticationFailedError("Invalid token header. Keyword mismatch.")

        user, _, session_id = await self.authenticate_user(jwt_token=auth[1])

        self.request.user_session_id = session_id
        self.scope['user_session_id'] = session_id
        self.scope['user'] = user

        return user

    @staticmethod
    def _get_jwt_payload_from_jwt_token(jwt_token: str, token_type: str):
        logger.debug("Logging via JWT auth. Got token: %s", jwt_token)
        try:
            # TODO: class-based JWT decoder
            jwt_payload = decode_jwt(jwt_token)
        except ExpiredSignatureError:
            logger.debug("JWT signature has been expired for token %s", jwt_token)
            raise SignatureExpiredError("JWT signature has been expired for token")
        except InvalidTokenError as error:
            msg = "Token could not be decoded: %s"
            logger.exception(msg, error)
            raise AuthenticationFailedError(msg % (error,))

        if jwt_payload["token_type"] != token_type:
            raise AuthenticationFailedError(
                f"Token type '{token_type}' expected, got '{jwt_payload['token_type']}' instead."
            )

        return jwt_payload

    async def authenticate_user(
        self,
        jwt_token: str,
        token_type: str = TOKEN_TYPE_ACCESS,
    ) -> Tuple[User, dict, str]:
        """Allows to find active user by jwt_token"""
        jwt_payload = self._get_jwt_payload_from_jwt_token(jwt_token, token_type)

        session_id = jwt_payload.get("session_id", "00000000-0000-0000-0000-000000000000")
        if not session_id:
            raise AuthenticationFailedError("Incorrect data in JWT: session_id is missed")

        user_id = jwt_payload.get("user_id")
        self.scope['user_id'] = user_id

        user = await User.get_active(self.db_session, user_id)
        if not user:
            msg = "Couldn't found active user with id=%s."
            logger.warning(msg, user_id)
            raise AuthenticationFailedError(details=(msg % (user_id,)))

        user_session = await UserSession.async_get(
            self.db_session,
            public_id=session_id,
            is_active=True,
            user_id=user.id,
        )
        if not user_session:
            raise AuthenticationFailedError(
                f"Couldn't found active session: {user_id=} | {session_id=}."
            )

        return user, jwt_payload, session_id
