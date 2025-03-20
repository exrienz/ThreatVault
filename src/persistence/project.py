from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entity import Environment, Project
from src.infrastructure.database import get_session


class ProjectRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session

    async def get_by_id_extend(self, project_id: UUID | None = None) -> Project | None:
        stmt = (
            select(Project)
            .options(
                selectinload(Project.environment).selectinload(Environment.products)
            )
            .where(Project.deleted_at.is_(None))
            .order_by(Project.created_at.desc())
        )
        if project_id:
            stmt = stmt.where(Project.id == project_id)
        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def get_all(self) -> Sequence[Project]:
        stmt = (
            select(Project)
            .where(Project.deleted_at.is_(None))
            .order_by(Project.created_at.desc())
        )
        query = await self.session.execute(stmt)
        return query.scalars().all()

    async def get_all_extend(self, project_id: UUID | None = None) -> Sequence[Project]:
        stmt = (
            select(Project)
            .options(
                selectinload(Project.environment).selectinload(Environment.products)
            )
            .where(Project.deleted_at.is_(None))
            .order_by(Project.created_at.desc())
        )
        if project_id:
            stmt = stmt.where(Project.id == project_id)
        query = await self.session.execute(stmt)
        return query.scalars().all()

    async def get(self, item_id: UUID) -> Project | None:
        stmt = select(Project).where(
            Project.id == item_id, Project.deleted_at.is_(None)
        )
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

        # TODO: Fix this
        for env in ["production", "non-production"]:
            env_data = {"name": env, "project_id": db_data.id}
            env_db = Environment(**env_data)
            self.session.add(env_db)

        await self.session.commit()
        await self.session.refresh(db_data)
        return db_data

    async def delete(self, item_id: UUID):
        item = await self.get(item_id)
        if not item:
            raise

        item.deleted_at = datetime.now()
        await self.session.commit()
