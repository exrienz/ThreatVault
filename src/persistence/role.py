from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity import Role
from src.infrastructure.database.session import get_session
from src.persistence.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    def __init__(self, session: AsyncSession = Depends(get_session)):
        super().__init__(Role, session)

    async def get_by_name(self, role_name: str) -> Role | None:
        stmt = select(Role).where(Role.name == role_name)
        query = await self.session.execute(stmt)
        return query.scalar()
