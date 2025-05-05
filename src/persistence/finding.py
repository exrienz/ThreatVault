import json
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import ARRAY, Select, String, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.constant import FnStatusEnum
from src.domain.entity import Finding, FindingName
from src.infrastructure.database import get_session
from src.persistence.base import BaseRepository, Pagination


class FindingRepository(BaseRepository):
    def __init__(self, session: Annotated[AsyncSession, Depends(get_session)]):
        super().__init__(Finding, session)

    def _options(self, stmt: Select):
        return stmt.options(selectinload(Finding.finding_name))

    async def get_by_product_id_extended(
        self,
        product_id: UUID,
        pagination: bool = False,
        page: int = 1,
    ):
        stmt = (
            select(Finding)
            .join(FindingName)
            .options(selectinload(Finding.finding_name))
            .where(
                FindingName.product_id == product_id,
                Finding.status != FnStatusEnum.CLOSED,
            )
        ).order_by(Finding.severity)
        if pagination:
            return await self.pagination(stmt, page, True)

        query = await self.session.execute(stmt)
        return query.scalars().all()

    async def get_latest_date_by_product_id(self, product_id: UUID):
        stmt = (
            select(Finding.last_update)
            .join(FindingName)
            .where(FindingName.product_id == product_id)
            .order_by(Finding.last_update.desc())
            .limit(1)
        )

        query = await self.session.execute(stmt)
        return query.scalar()

    async def get_group_by_severity_status(
        self,
        product_id: UUID,
        page: int = 1,
        filters: dict | str | None = None,
    ) -> Pagination:
        stmt = (
            select(
                FindingName.id.label("finding_name_id"),
                FindingName.name,
                Finding.severity,
                Finding.status,
                func.max(Finding.remark),
                func.max(Finding.finding_date),
                func.array_agg(func.distinct(Finding.host), type_=ARRAY(String)).label(
                    "hosts"
                ),
            )
            .join(FindingName)
            .where(
                FindingName.product_id == product_id,
            )
        )
        if isinstance(filters, str):
            filters = json.loads(filters)
        if isinstance(filters, dict):
            for k, v in filters.items():
                if not v:
                    continue
                stmt = stmt.where(getattr(Finding, k).in_(v))
        stmt = stmt.group_by(FindingName.id, Finding.severity, Finding.status).order_by(
            Finding.severity
        )
        return await self.pagination(stmt, page)

    async def update(self, item_id: UUID, data: dict, hosts: list):
        stmt = (
            update(Finding)
            .where(
                Finding.host.in_(hosts),
                Finding.finding_name_id == item_id,
                Finding.status != FnStatusEnum.CLOSED,
            )
            .values(data)
        )
        await self.session.execute(stmt)
        await self.session.commit()
