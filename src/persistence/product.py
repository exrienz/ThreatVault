from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entity import Environment, Product
from src.infrastructure.database import get_session


class ProductRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session

    async def get_by_id(self, item_id: UUID):
        stmt = (
            select(Product)
            .where(Product.id == item_id, Product.deleted_at.is_(None))
            .options(selectinload(Product.environment))
        )
        query = await self.session.execute(stmt)
        return query.scalars().one_or_none()

    async def delete(self, item_id: UUID):
        product = await self.get_by_id(item_id)
        if product is None:
            raise
        product.deleted_at = datetime.now()
        await self.session.commit()

    async def create(self, data: dict) -> Product:
        db_data = Product(**data)
        self.session.add(db_data)
        await self.session.commit()
        await self.session.refresh(db_data)
        return db_data

    async def get_by_id_filter(
        self,
        project_id: UUID | None = None,
        environment_id: UUID | None = None,
    ) -> Sequence[Product]:
        stmt = (
            select(Product)
            .join(Environment)
            .where(
                Environment.deleted_at.is_(None),
                Product.deleted_at.is_(None),
            )
        )
        if project_id:
            stmt = stmt.where(Environment.project_id == project_id)
        if environment_id:
            stmt = stmt.where(Environment.id == environment_id)
        query = await self.session.execute(stmt)
        return query.scalars().all()
