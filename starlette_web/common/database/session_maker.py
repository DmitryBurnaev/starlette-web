from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from starlette_web.common.conf import settings


def make_session_maker() -> sessionmaker:
    db_engine = create_async_engine(settings.DATABASE_DSN, echo=settings.DB_ECHO)
    return sessionmaker(
        db_engine,
        expire_on_commit=False,
        class_=AsyncSession,
        autoflush=True,
        autocommit=False,
    )
