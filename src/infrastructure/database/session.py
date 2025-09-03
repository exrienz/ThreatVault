from collections.abc import AsyncIterator, Iterator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from .config import AsyncSessionFactory, SyncSessionFactory


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_session() -> Iterator[Session]:
    with SyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
