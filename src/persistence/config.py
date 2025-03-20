from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity import GlobalConfig
from src.infrastructure.database import get_session


class GlobalRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session

    async def get(self) -> GlobalConfig | None:
        stmt = select(GlobalConfig)
        query = await self.session.execute(stmt)
        return query.scalars().first()
