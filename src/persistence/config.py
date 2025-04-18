from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity import GlobalConfig
from src.infrastructure.database import get_session
from src.persistence.base import BaseRepository


class GlobalRepository(BaseRepository[GlobalConfig]):
    def __init__(self, session: AsyncSession = Depends(get_session)):
        super().__init__(GlobalConfig, session)

    async def get(self) -> GlobalConfig | None:
        stmt = select(GlobalConfig)
        query = await self.session.execute(stmt)
        return query.scalars().first()
