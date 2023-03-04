# flake8: noqa E402
import os

os.environ.setdefault("STARLETTE_SETTINGS_MODULE", "starlette_web.core.settings")

import asyncio
import sys
import uuid
from datetime import datetime, timedelta
from typing import Tuple
from unittest.mock import patch, AsyncMock

import pytest
import sqlalchemy
from sqlalchemy.engine import URL
from sqlalchemy.util import concurrency
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import ProgrammingError, OperationalError

from starlette_web.common import database
from starlette_web.common.conf import settings
from starlette_web.contrib.auth.models import UserInvite
from starlette_web.tests.helpers import (
    WebTestClient,
    get_user_data,
    create_user,
    mock_target_class,
    create_user_session,
    make_db_session,
    await_,
)
from starlette_web.tests.mocks import MockProcess


if (*sys.version_info,) >= (3, 8) and sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


@pytest.fixture(autouse=True, scope="session")
def test_settings():
    settings.APP_DEBUG = True
    settings.MAX_UPLOAD_ATTEMPT = 1
    settings.RETRY_UPLOAD_TIMEOUT = 0


@pytest.fixture(autouse=True, scope="session")
def config():
    from starlette_web.contrib.constance import config as base_config

    settings.CONSTANCE_CONFIG = {
        "TEST_CONSTANT_1": (1, "Test constant 1", int),
        "TEST_CONSTANT_2": (2, "Test constant 2", int),
        "TEST_CONSTANT_UUID": (
            uuid.UUID("094eb5ff-01de-4985-afeb-22ebb9e76abf"),
            "Test constant uuid",
            uuid.UUID,
        ),
        "TEST_CONSTANT_DATETIME": (datetime(2000, 1, 1), "Test constant datetime", datetime),
    }
    settings.CONSTANCE_BACKEND = "starlette_web.contrib.constance.backends.database.DatabaseBackend"

    base_config._setup()
    yield base_config


@pytest.fixture(autouse=True, scope="session")
def client() -> WebTestClient:
    from starlette_web.common.app import get_app

    with WebTestClient(get_app(run_checks_on_startup=False)) as client:
        with make_db_session(asyncio.get_event_loop_policy().get_event_loop()) as db_session:
            client.db_session = db_session
            yield client


@pytest.fixture
def dbs(loop) -> AsyncSession:
    with make_db_session(loop) as db_session:
        yield db_session


def db_prep():
    print("Dropping the old test db…")
    postgres_db_dsn = URL.create(
        drivername="postgresql",
        username=settings.DATABASE["username"],
        password=settings.DATABASE["password"],
        host=settings.DATABASE["host"],
        port=settings.DATABASE["port"],
        database="postgres",
    )
    engine = sqlalchemy.create_engine(postgres_db_dsn)
    conn = engine.connect()

    def exec_sql(query: str):
        conn.execute(sqlalchemy.text(query))

    try:
        conn = conn.execution_options(autocommit=False)
        exec_sql("ROLLBACK")
        exec_sql(f"DROP DATABASE {settings.DB_NAME}")
    except ProgrammingError:
        print("Could not drop the database, probably does not exist.")
        exec_sql("ROLLBACK")
    except OperationalError:
        print("Could not drop database because it’s being accessed by other users")
        exec_sql("ROLLBACK")

    print(f"Test db dropped! about to create {settings.DB_NAME}")
    exec_sql(f"CREATE DATABASE {settings.DB_NAME}")
    username, password = settings.DATABASE["username"], settings.DATABASE["password"]

    try:
        exec_sql(f"CREATE USER {username} WITH ENCRYPTED PASSWORD '{password}'")
    except Exception as e:
        print(f"User already exists. ({e})")
        exec_sql(f"GRANT ALL PRIVILEGES ON DATABASE {settings.DB_NAME} TO {username}")

    conn.close()


@pytest.fixture(autouse=True, scope="session")
def db_migration():
    def create_tables():
        db_prep()
        print("Creating tables...")
        engine = sqlalchemy.create_engine(settings.DATABASE_DSN)
        database.ModelBase.metadata.create_all(engine)

    await_(concurrency.greenlet_spawn(create_tables))
    print("DB and tables were successful created.")


@pytest.fixture
def mocked_process(monkeypatch) -> MockProcess:
    yield from mock_target_class(MockProcess, monkeypatch)


@pytest.fixture
def mocked_auth_send() -> AsyncMock:
    mocked_send_email = AsyncMock()
    patcher = patch("starlette_web.contrib.auth.views.send_email", new=mocked_send_email)
    patcher.start()
    yield mocked_send_email
    del mocked_send_email
    patcher.stop()


@pytest.fixture()
def user_data() -> Tuple[str, str]:
    return get_user_data()


@pytest.fixture
def loop():
    return asyncio.get_event_loop_policy().get_event_loop()


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
