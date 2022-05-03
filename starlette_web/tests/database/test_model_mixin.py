import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from starlette_web.auth.models import User
from starlette_web.tests.helpers import await_


def test_async_create(dbs: AsyncSession):
    email = str(uuid.uuid4()).replace('-', '') + '@test.com'
    password = User.make_password(str(uuid.uuid4()))

    user = await_(User.async_get(db_session=dbs, email=email, password=password))
    assert user is None

    user = await_(User.async_create(db_session=dbs, email=email, password=password))
    assert user is not None
    assert type(user) == User
    assert user.id is not None

    user = await_(User.async_get(db_session=dbs, email=email, password=password))
    assert user is not None


def test_async_update(dbs: AsyncSession):
    email = str(uuid.uuid4()).replace('-', '') + '@test.com'
    password = User.make_password(str(uuid.uuid4()))
    user = await_(User.async_create(db_session=dbs, email=email, password=password))

    email = str(uuid.uuid4()).replace('-', '') + '@test.com'
    password = User.make_password(str(uuid.uuid4()))
    await_(User.async_update(
        db_session=dbs,
        filter_kwargs={'id': user.id},
        update_data={'email': email, 'password': password},
    ))

    user = await_(User.async_get(db_session=dbs, id=user.id))
    assert user.email == email
    assert user.password == password


def test_async_filter(dbs: AsyncSession):
    email = str(uuid.uuid4()).replace('-', '') + '@test.com'
    password = User.make_password(str(uuid.uuid4()))
    _ = await_(User.async_create(db_session=dbs, email=email, password=password))

    email = str(uuid.uuid4()).replace('-', '') + '@test.com'
    password = User.make_password(str(uuid.uuid4()))
    _ = await_(User.async_create(db_session=dbs, email=email, password=password))

    users = (await_(User.async_filter(db_session=dbs))).all()
    assert len(users) >= 2
    assert type(users[0]) == User


def test_async_create_or_update(dbs: AsyncSession):
    email = str(uuid.uuid4()).replace('-', '') + '@test.com'
    password = User.make_password(str(uuid.uuid4()))

    user = await_(User.async_get(db_session=dbs, email=email, password=password))
    assert user is None

    user = await_(User.async_create_or_update(
        db_session=dbs,
        filter_kwargs={'email': email, 'password': password},
        update_data={},
    ))
    user_id = user.id
    assert user is not None
    assert type(user) == User
    assert user.email == email
    assert user.password == password
    assert user.id is not None

    user = await_(User.async_create_or_update(
        db_session=dbs,
        filter_kwargs={'email': email, 'password': password},
        update_data={'is_active': True, 'is_superuser': True},
    ))
    assert user is not None
    assert type(user) == User
    assert user.id == user_id
    assert user.is_superuser

    new_email = str(uuid.uuid4()).replace('-', '') + '@test.com'
    new_password = User.make_password(str(uuid.uuid4()))
    user = await_(User.async_create_or_update(
        db_session=dbs,
        filter_kwargs={'email': email, 'password': password},
        update_data={'email': new_email, 'password': new_password},
    ))
    assert user.id == user_id
    assert user.email == new_email
    assert user.password == new_password


def test_async_get_or_create(dbs: AsyncSession):
    email = str(uuid.uuid4()).replace('-', '') + '@test.com'
    password = User.make_password(str(uuid.uuid4()))
    user = await_(User.async_get_or_create(
        db_session=dbs, filter_kwargs={'email': email, 'password': password}))
    user_id = user.id

    assert user is not None
    assert type(user) == User
    assert user.email == email
    assert user.password == password
    assert not user.is_superuser
    assert user_id is not None

    user = await_(User.async_get_or_create(
        db_session=dbs, filter_kwargs={'email': email, 'password': password}))
    assert user.id == user_id

    email = str(uuid.uuid4()).replace('-', '') + '@test.com'
    password = User.make_password(str(uuid.uuid4()))
    user = await_(User.async_get_or_create(
        db_session=dbs,
        filter_kwargs={'email': email, 'password': password},
        extra_data={'is_superuser': True},
    ))
    assert user is not None
    assert type(user) == User
    assert user.is_superuser
    assert user.id is not None
