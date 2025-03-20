from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.constant import SeverityEnum
from src.domain.entity import Finding, FindingName, Product
from src.infrastructure.database import get_session


class FindingNameRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session

    async def updateFindingName(self, finding_name: str, product_id: UUID):
        try:
            data = FindingName(name=finding_name, product_id=product_id)
            self.session.add(data)
            await self.session.commit()
        # TODO: Can have integrityError: Need to handle
        except IntegrityError:
            pass

    async def get_by_filter(
        self, finding_name_id: UUID | None = None, severity: SeverityEnum | None = None
    ):
        stmt = (
            select(FindingName)
            .join(Finding)
            .join(Product)
            .options(
                selectinload(FindingName.findings), selectinload(FindingName.product)
            )
        )

        if finding_name_id:
            stmt = stmt.where(FindingName.id == finding_name_id)
        if severity:
            stmt = stmt.where(Finding.severity == severity)
        query = await self.session.execute(stmt)
        return query.scalars().first()
