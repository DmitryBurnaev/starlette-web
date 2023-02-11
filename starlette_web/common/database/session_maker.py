from typing import Type

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from starlette_web.common.conf import settings
from starlette_web.common.utils import import_string


def get_async_session_class() -> Type[AsyncSession]:
    return import_string(settings.DB_ASYNC_SESSION_CLASS)


def make_session_maker(**kwargs) -> sessionmaker:
    use_pool = kwargs.get("use_pool", True)
    connect_args = kwargs.get("connect_args", {"timeout": 20})

    if use_pool:
        pool_size = settings.DATABASE["pool_min_size"]
        max_overflow = max(0, settings.DATABASE["pool_max_size"] - pool_size)

        # If poolclass is None, uses one implemented by engine's method .get_pool_class()
        # Namely, for asyncpg, sqlalchemy.pool.impl.AsyncAdaptedQueuePool
        create_async_engine_kw = dict(
            poolclass=None,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=settings.DB_POOL_RECYCLE,
        )
    else:
        create_async_engine_kw = dict(
            poolclass=NullPool,
        )

    db_engine = create_async_engine(
        settings.DATABASE_DSN,
        echo=settings.DB_ECHO,
        connect_args=connect_args,
        **create_async_engine_kw,
    )

    return sessionmaker(
        db_engine,
        expire_on_commit=False,
        class_=get_async_session_class(),
        autoflush=True,
        autocommit=False,
    )
