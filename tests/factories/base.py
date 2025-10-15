import factory
from sqlalchemy.ext.asyncio import AsyncSession


class AsyncSQLAlchemyFactory(factory.Factory):
    """Factory base that supports async SQLAlchemy sessions."""

    @classmethod
    async def async_prep(cls, session, kwargs):
        return kwargs

    @classmethod
    async def create_async(cls, session: AsyncSession, **kwargs):
        if hasattr(cls, "async_prep"):
            kwargs = await cls.async_prep(session, kwargs)

        obj = cls.build(**kwargs)  # only builds, doesn't persist
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj
