from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy import update as SQL_UPDATE
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity import CVE
from src.infrastructure.database import get_session
from src.infrastructure.database.config import SyncSessionFactory
from src.persistence.base import BaseRepository


class CVERepository(BaseRepository[CVE]):
    def __init__(self, session: Annotated[AsyncSession, Depends(get_session)]):
        super().__init__(CVE, session)

    async def get_cves_without_priority(self):
        stmt = select(CVE).where(CVE.priority.is_(None), CVE.name.isnot(None))
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def update_bulk(self, data: list):
        stmt = SQL_UPDATE(CVE)
        await self.session.execute(stmt, data)
        await self.session.commit()

    def sync_get_cves_without_priority(self):
        stmt = select(CVE).where(CVE.priority.is_(None), CVE.name.isnot(None))
        with SyncSessionFactory() as session:
            result = session.execute(stmt)
            return result.scalars().all()
