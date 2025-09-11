from uuid import UUID

from fastapi import Depends
from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entity import Finding, FindingName, Product
from src.infrastructure.database import get_session
from src.persistence.base import AdvFilterType, BaseRepository


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

    def _options(self, stmt: Select) -> Select:
        return stmt.options(selectinload(FindingName.findings))

    async def get_by_filter(self, filters: dict) -> FindingName | None:
        stmt = (
            select(FindingName)
            .join(Finding)
            .join(Product)
            .options(selectinload(FindingName.findings), selectinload(Finding.product))
        )

        flt = {
            "finding_name_id": FindingName.id,
            "severity": Finding.severity,
            "name": FindingName.name.ilike,
            "product_id": Finding.product_id,
        }
        _filters: AdvFilterType = {}
        for k, v in filters.items():
            filter_map = flt.get(k)
            if filter_map is None:
                continue
            _filters[filter_map] = v

        stmt = self._advanced_filtering(stmt, _filters)
        query = await self.session.execute(stmt)
        return query.scalars().first()
