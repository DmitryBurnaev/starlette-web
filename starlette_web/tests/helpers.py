import asyncio
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from hashlib import blake2b
from typing import Tuple, Type
from unittest import mock

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.testclient import TestClient

from starlette_web.common.database import make_session_maker
from starlette_web.contrib.auth.utils import encode_jwt
from starlette_web.contrib.auth.models import User, UserSession
from starlette_web.tests.mocks import BaseMock


class WebTestClient(TestClient):
    db_session: AsyncSession = None

    def login(self, user: User):
        user_session = create_user_session(self.db_session, user)
        jwt, _ = encode_jwt({"user_id": user.id, "session_id": user_session.public_id})
        self.headers["Authorization"] = f"Bearer {jwt}"
        return user_session

    def logout(self):
        self.headers.pop("Authorization", None)


def await_(coroutine):
    """Run coroutine in the current event loop"""

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coroutine)


def mock_target_class(mock_class: Type[BaseMock], monkeypatch):
    """Allows to mock any classes (is used as fixture)

    # in conftest.py:
    >>> import pytest
    >>> @pytest.fixture
    >>> def mocked_bicycle(monkeypatch) -> MockBicycle: # noqa
    >>>     yield from mock_target_class(MockBicycle, monkeypatch) # noqa

    # in test.py:
    >>> def test_something(mocked_sender):
    >>>     mocked_bicycle.run.assert_called
    >>>     mocked_bicycle.target_class.__init__.assert_called
    """

    mock_obj = mock_class()

    def init_method(target_obj=None, *args, **kwargs):
        nonlocal mock_obj
        mock_obj.target_obj = target_obj
        mock_obj.mock_init(*args, **kwargs)

    with mock.patch.object(mock_class.target_class, "__init__", autospec=True) as init:
        init.side_effect = init_method
        for mock_method in mock_obj.get_mocks():
            monkeypatch.setattr(
                mock_class.target_class, mock_method, getattr(mock_obj, mock_method)
            )

        yield mock_obj

    del mock_obj


def get_user_data() -> Tuple[str, str]:
    return f"u_{uuid.uuid4().hex[:10]}@test.com", "password"


def get_source_id() -> str:
    """Generate SourceID (ex.: youtube's video-id)"""
    return blake2b(key=bytes(str(time.time()), encoding="utf-8"), digest_size=6).hexdigest()[:11]


@contextmanager
def make_db_session(loop):
    session_maker = make_session_maker()
    async_session = session_maker()
    await_(async_session.__aenter__())
    yield async_session
    await_(async_session.__aexit__(None, None, None))


def create_user(db_session):
    email, password = get_user_data()
    return await_(User.async_create(db_session, db_commit=True, email=email, password=password))


def create_user_session(db_session, user):
    return await_(
        UserSession.async_create(
            db_session,
            db_commit=True,
            user_id=user.id,
            public_id=str(uuid.uuid4()),
            refresh_token="refresh-token",
            is_active=True,
            expired_at=datetime.utcnow() + timedelta(seconds=120),
            created_at=datetime.utcnow(),
            refreshed_at=datetime.utcnow(),
        )
    )
