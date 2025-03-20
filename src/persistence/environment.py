from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.domain.entity import Environment
from src.infrastructure.database.session import get_session


class EnvRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session

    async def get_all(self):
        stmt = (
            select(Environment)
            .options(joinedload(Environment.project))
            .options(joinedload(Environment.products))
        )
        query = await self.session.execute(stmt)
        return query.scalars().all()

    async def get_by_filter(
        self,
        name: str | None = None,
        project_id: UUID | None = None,
    ) -> Environment | None:
        stmt = select(Environment)
        if name:
            stmt = stmt.where(Environment.name == name)
        if project_id:
            stmt = stmt.where(Environment.project_id == project_id)
        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def get_all_by_filter(
        self,
        name: str | None = None,
        project_id: UUID | None = None,
    ):
        stmt = select(Environment)
        if name:
            stmt = stmt.where(Environment.name == name)
        if project_id:
            stmt = stmt.where(Environment.project_id == project_id)
        query = await self.session.execute(stmt)
        return query.scalars().all()

    async def create(self, data: dict):
        db_data = Environment(**data)
        self.session.add(db_data)
        await self.session.commit()
        await self.session.refresh(db_data)

    async def create_bulk(self, data_list: list[dict], commit: bool = True):
        db_list = []
        for data in data_list:
            db_list.append(Environment(**data))
        self.session.add_all(db_list)
        if commit:
            await self.session.commit()
