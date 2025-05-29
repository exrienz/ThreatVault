from fastapi import Depends
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entity import Role, User
from src.infrastructure.database import get_session
from src.persistence.base import BaseRepository


class AuthRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession = Depends(get_session)):
        super().__init__(User, session)

    async def register(self, data: dict) -> User:
        await self.assign_role_and_activation(data)
        db_data = User(**data)
        await self.register_validation(db_data.username, db_data.email)
        self.session.add(db_data)
        await self.session.commit()
        await self.session.refresh(db_data)
        return db_data

    async def assign_role_and_activation(self, data: dict):
        role, active = "Owner", False
        usr_stmt = select(func.count(User.id))
        query = await self.session.execute(usr_stmt)
        user_cnt = query.scalar_one()
        if user_cnt == 0:
            role = "Admin"
            active = True
        role_stmt = select(Role.id).where(Role.name == role)
        query = await self.session.execute(role_stmt)
        role_id = query.scalar_one()

        data["role_id"] = role_id
        data["active"] = active

    async def register_validation(self, username: str, email: str):
        stmt = select(User).where(
            or_(User.username.ilike(username), User.email.ilike(email))
        )
        query = await self.session.execute(stmt)
        user = query.scalars().first()
        if user:
            raise

    def _options(self, stmt: Select):
        return stmt.options(selectinload(User.role))
