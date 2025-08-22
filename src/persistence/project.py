from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entity import Environment, Project
from src.infrastructure.database import get_session
from src.persistence.base import BaseRepository
from src.presentation.dependencies import get_allowed_project_ids


class ProjectRepository(BaseRepository[Project]):
    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(get_session)],
        project_ids: Annotated[list[UUID], Depends(get_allowed_project_ids)],
    ):
        super().__init__(Project, session, project_ids)

    def _options(self, stmt: Select):
        return stmt.options(
            selectinload(Project.environment).selectinload(Environment.products)
        )

    async def get(self, item_id: UUID) -> Project | None:
        stmt = select(Project).where(Project.id == item_id)
        stmt = self._options(stmt)
        query = await self.session.execute(stmt)
        return query.scalars().one_or_none()

    async def create(self, data: dict, commit: bool = True) -> Project:
        db_data = Project(**data)
        self.session.add(db_data)
        if commit:
            await self.session.commit()
            await self.session.refresh(db_data)
        return db_data

    async def create_with_env(self, data: dict) -> Project:
        db_data = await self.create(data, commit=False)
        await self.session.flush()

        for env in ["production", "non-production"]:
            env_data = {"name": env, "project_id": db_data.id}
            env_db = Environment(**env_data)
            self.session.add(env_db)

        await self.session.commit()
        await self.session.refresh(db_data)
        return db_data

    async def min_year(self) -> int | None:
        stmt = (
            select(func.extract("year", Project.created_at))
            .order_by(Project.created_at)
            .limit(1)
        )
        query = await self.session.execute(stmt)
        return query.scalars().one_or_none()

    def _product_allowed_ids(self, stmt: Select) -> Select:
        return super()._product_allowed_ids(stmt)

    def _project_allowed_ids(self, stmt: Select) -> Select:
        if self.allowed_project_ids is None:
            return stmt
        return stmt.where(Project.id.in_(self.allowed_project_ids))
