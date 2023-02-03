import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from starlette_web.common.database.transaction import AtomicTransaction
from starlette_web.contrib.auth.models import User
from starlette_web.tests.helpers import await_


def test_nested_transaction(dbs: AsyncSession):
    email = str(uuid.uuid4()).replace("-", "") + "@test.com"
    password = User.make_password(str(uuid.uuid4()))

    block1_wrapper = None
    block2_wrapper = None

    block_1_exited = False
    block_2_exited = False

    try:
        block1_wrapper = dbs.begin_nested()
        block1 = await_(block1_wrapper.__aenter__())

        block2_wrapper = dbs.begin_nested()
        block2 = await_(block2_wrapper.__aenter__())
        _ = await_(User.async_create(db_session=dbs, email=email, password=password))

        user = await_(User.async_get(db_session=dbs, email=email, password=password))
        assert user is not None
        await_(block2.commit())
        await_(block2_wrapper.__aexit__(None, None, None))
        block_2_exited = True

        user = await_(User.async_get(db_session=dbs, email=email, password=password))
        assert user is not None
        await_(block1.rollback())
        await_(block1_wrapper.__aexit__(None, None, None))
        block_1_exited = True

        user = await_(User.async_get(db_session=dbs, email=email, password=password))
        assert user is None
    finally:
        if block2_wrapper and not block_2_exited:
            await_(block2_wrapper.__aexit__(None, None, None))

        if block1_wrapper and not block_1_exited:
            await_(block1_wrapper.__aexit__(None, None, None))


def test_atomic_transaction(dbs: AsyncSession):
    async def atomic_coroutine(user_obj, db_session):
        async with AtomicTransaction(db_session=db_session):
            _ = await User.async_create(db_session=dbs, **user_obj)

        user = await User.async_get(db_session=dbs, **user_obj)
        return user

    email = str(uuid.uuid4()).replace("-", "") + "@test.com"
    password = User.make_password(str(uuid.uuid4()))
    user = await_(atomic_coroutine({"email": email, "password": password}, db_session=dbs))
    assert user is not None


def test_nested_atomic_transactions(dbs: AsyncSession):
    async def atomic_coroutine(user_obj_1, user_obj_2, db_session):
        async with AtomicTransaction(db_session=db_session):
            _ = await User.async_create(db_session=dbs, **user_obj_1)

            try:
                async with AtomicTransaction(db_session=db_session):
                    _ = await User.async_create(db_session=dbs, **user_obj_2)
                    raise Exception("Unexpected error")
            except:  # noqa: E722
                pass

        user1 = await User.async_get(db_session=dbs, **user_obj_1)
        user2 = await User.async_get(db_session=dbs, **user_obj_2)
        return user1, user2

    email1 = str(uuid.uuid4()).replace("-", "") + "@test.com"
    password1 = User.make_password(str(uuid.uuid4()))
    user_obj_1 = {"email": email1, "password": password1}

    email2 = str(uuid.uuid4()).replace("-", "") + "@test.com"
    password2 = User.make_password(str(uuid.uuid4()))
    user_obj_2 = {"email": email2, "password": password2}

    user1, user2 = await_(atomic_coroutine(user_obj_1, user_obj_2, db_session=dbs))
    assert user1 is not None
    assert user2 is None
