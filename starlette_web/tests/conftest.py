import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Tuple
from unittest.mock import patch, AsyncMock

import pytest
from alembic.config import main
from sqlalchemy.ext.asyncio import AsyncSession

from starlette_web.core import settings
from starlette_web.auth.models import UserInvite
from starlette_web.tests.helpers import (
    WebTestClient,
    get_user_data,
    create_user,
    mock_target_class,
    create_user_session,
    make_db_session,
)
from starlette_web.tests.mocks import MockProcess


@pytest.fixture(autouse=True, scope="session")
def test_settings():
    settings.APP_DEBUG = True
    settings.MAX_UPLOAD_ATTEMPT = 1
    settings.RETRY_UPLOAD_TIMEOUT = 0


@pytest.fixture(autouse=True)
def cap_log(caplog):
    # trying to print out logs for failed tests
    caplog.set_level(logging.INFO)
    logging.getLogger("modules").setLevel(logging.INFO)


@pytest.fixture(autouse=True, scope="session")
def client() -> WebTestClient:
    from core.app import get_app

    with WebTestClient(get_app()) as client:
        with make_db_session(asyncio.get_event_loop()) as db_session:
            client.db_session = db_session
            yield client


@pytest.fixture
def dbs(loop) -> AsyncSession:
    with make_db_session(loop) as db_session:
        yield db_session


@pytest.fixture(autouse=True, scope="session")
def db_migration():
    ini_path = settings.PROJECT_ROOT_DIR / "alembic.ini"
    main(["--raiseerr", f"-c{ini_path}", "upgrade", "head"])


@pytest.fixture
def mocked_process(monkeypatch) -> MockProcess:
    yield from mock_target_class(MockProcess, monkeypatch)


@pytest.fixture
def mocked_auth_send() -> AsyncMock:
    mocked_send_email = AsyncMock()
    patcher = patch("modules.auth.views.send_email", new=mocked_send_email)
    patcher.start()
    yield mocked_send_email
    del mocked_send_email
    patcher.stop()


@pytest.fixture()
def user_data() -> Tuple[str, str]:
    return get_user_data()


@pytest.fixture
def loop():
    return asyncio.get_event_loop()


@pytest.fixture
def user(dbs):
    return create_user(dbs)


@pytest.fixture
def user_session(user, loop, dbs):
    return create_user_session(dbs, user)


@pytest.fixture
def user_invite(user, loop, dbs) -> UserInvite:
    return loop.run_until_complete(
        UserInvite.async_create(
            dbs,
            db_commit=True,
            email=f"user_{uuid.uuid4().hex[:10]}@test.com",
            token=f"{uuid.uuid4().hex}",
            expired_at=datetime.utcnow() + timedelta(days=1),
            owner_id=user.id,
        )
    )
