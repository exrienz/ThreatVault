from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entity import Finding, FindingName, Product
from src.infrastructure.database import get_session
from src.persistence.base import BaseRepository


class FindingNameRepository(BaseRepository[FindingName]):
    def __init__(self, session: AsyncSession = Depends(get_session)):
        super().__init__(FindingName, session)

    async def updateFindingName(self, finding_name: str, product_id: UUID):
        try:
            data = FindingName(name=finding_name, product_id=product_id)
            self.session.add(data)
            await self.session.commit()
        # TODO: Can have integrityError: Need to handle
        except IntegrityError:
            pass

    async def get_by_filter(self, filters: dict) -> FindingName | None:
        stmt = (
            select(FindingName)
            .join(Finding)
            .join(Product)
            .options(
                selectinload(FindingName.findings), selectinload(FindingName.product)
            )
        )

        if finding_name_id := filters.get("finding_name_id"):
            stmt = stmt.where(FindingName.id == finding_name_id)
        if severity := filters.get("severity"):
            stmt = stmt.where(Finding.severity == severity)
        query = await self.session.execute(stmt)
        return query.scalars().first()
