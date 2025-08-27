from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity.project_management import ProductEscalationPoint
from src.domain.entity.user_access import User
from src.infrastructure.database import get_session
from src.persistence.base import BaseRepository


class ProductEscalationRepository(BaseRepository[ProductEscalationPoint]):
    def __init__(self, session: Annotated[AsyncSession, Depends(get_session)]):
        super().__init__(ProductEscalationPoint, session)

    async def delete_update(self, product_id: UUID, user_ids: list[UUID]):
        del_stmt = delete(ProductEscalationPoint).where(
            ProductEscalationPoint.product_id == product_id
        )
        await self.session.execute(del_stmt)

        data_list = [
            {"product_id": product_id, "user_id": user_id} for user_id in user_ids
        ]
        await self.create_bulk(data_list)

    async def get_escalated_user(self, product_id: UUID) -> Sequence[User]:
        stmt = (
            select(User)
            .join(ProductEscalationPoint)
            .where(ProductEscalationPoint.product_id == product_id)
        )

        query = await self.session.execute(stmt)
        return query.scalars().all()
