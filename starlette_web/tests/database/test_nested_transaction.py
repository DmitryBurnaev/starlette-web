import uuid

from sqlalchemy.ext.asyncio import AsyncSession

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
        # Note: With .begin_nested(), calling .commit()/.rollback() at end is obligatory
        await_(block2.commit())
        await_(block2_wrapper.__aexit__(None, None, None))
        block_2_exited = True

        user = await_(User.async_get(db_session=dbs, email=email, password=password))
        assert user is not None
        # Note: With .begin_nested(), calling .commit()/.rollback() at end is obligatory
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
