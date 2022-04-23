import datetime
from typing import TypeVar

from sqlalchemy import and_, select, update, delete
from sqlalchemy.engine import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select


class ModelMixin:
    """Base model for Gino (sqlalchemy) ORM"""

    id: int = NotImplemented

    class Meta:
        order_by = ("id",)

    @classmethod
    def prepare_query(cls, limit: int = None, offset: int = None, **filter_kwargs) -> Select:
        order_by = []
        for field in cls.Meta.order_by:
            if field.startswith("-"):
                order_by.append(getattr(cls, field.replace("-", "")).desc())
            else:
                order_by.append(getattr(cls, field))

        query = select(cls).filter(cls._filter_criteria(filter_kwargs)).order_by(*order_by)
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)

        return query

    @classmethod
    async def async_filter(
        cls, db_session: AsyncSession, limit: int = None, offset: int = None, **filter_kwargs
    ) -> ScalarResult:
        query = cls.prepare_query(limit=limit, offset=offset, **filter_kwargs)
        result = await db_session.execute(query)
        return result.scalars()

    @classmethod
    async def async_get(cls, db_session: AsyncSession, **filter_kwargs) -> "DBModel":
        query = cls.prepare_query(**filter_kwargs)
        result = await db_session.execute(query)
        return result.scalars().first()

    @classmethod
    async def async_update(cls, db_session: AsyncSession, filter_kwargs: dict, update_data: dict):
        query = (
            update(cls)
            .where(cls._filter_criteria(filter_kwargs))
            .values(**update_data)
            .execution_options(synchronize_session="fetch")
        )
        await db_session.execute(query)

    @classmethod
    async def async_delete(cls, db_session: AsyncSession, filter_kwargs: dict):
        query = (
            delete(cls)
            .where(cls._filter_criteria(filter_kwargs))
            .execution_options(synchronize_session="fetch")
        )
        await db_session.execute(query)

    @classmethod
    async def async_create(cls, db_session: AsyncSession, db_commit=False, **data):
        instance = cls(**data)  # noqa
        db_session.add_all([instance])
        await db_session.flush()
        if db_commit:
            await db_session.commit()
        return instance

    async def update(self, db_session: AsyncSession, **update_data):
        if hasattr(self, "updated_at"):
            update_data["updated_at"] = datetime.datetime.utcnow()
        await self.async_update(db_session, {"id": self.id}, update_data=update_data)

    async def delete(self, db_session: AsyncSession):
        await db_session.delete(self)
        await db_session.flush()

    def to_dict(self, excluded_fields: list[str] = None) -> dict:
        excluded_fields = excluded_fields or []
        res = {}
        for field in self.__dict__:
            if field not in excluded_fields and not field.startswith("_"):
                res[field] = getattr(self, field)

        return res

    @classmethod
    def _filter_criteria(cls, filter_kwargs):
        filters = []
        for filter_name, filter_value in filter_kwargs.items():
            field, _, criteria = filter_name.partition("__")
            if criteria in ("eq", ""):
                filters.append(getattr(cls, field) == filter_value)
            elif criteria == "gt":
                filters.append(getattr(cls, field) > filter_value)
            elif criteria == "lt":
                filters.append(getattr(cls, field) < filter_value)
            elif criteria == "is":
                filters.append(getattr(cls, field).is_(filter_value))
            elif criteria == "in":
                filters.append(getattr(cls, field).in_(filter_value))
            elif criteria == "inarr":
                filters.append(getattr(cls, field).contains([filter_value]))
            elif criteria == "icontains":
                filters.append(getattr(cls, field).ilike(f"%{filter_value}%"))
            elif criteria == "ne":
                filters.append(getattr(cls, field) != filter_value)
            else:
                raise NotImplementedError(f"Unexpected criteria: {criteria}")

        return and_(True, *filters)


DBModel = TypeVar("DBModel", bound=ModelMixin)
