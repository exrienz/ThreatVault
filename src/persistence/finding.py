from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import (
    ARRAY,
    Select,
    String,
    case,
    func,
    select,
    update,
)
from sqlalchemy import (
    delete as sql_delete,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.constant import FnStatusEnum, SeverityEnum
from src.domain.entity import Finding, FindingName
from src.domain.entity.setting import GlobalConfig
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
        product_id: UUID | None = None,
        filters: dict | None = None,
        page: int = 1,
    ) -> Pagination:
        stmt = (
            (
                select(
                    FindingName.id.label("finding_name_id"),
                    FindingName.name,
                    Finding.severity,
                    Finding.status,
                    func.max(Finding.remark),
                    func.max(Finding.finding_date),
                    func.array_agg(
                        func.distinct(Finding.host), type_=ARRAY(String)
                    ).label("hosts"),
                ).join(FindingName)
            )
            .group_by(FindingName.id, Finding.severity, Finding.status)
            .order_by(Finding.severity)
        )
        if product_id:
            stmt = stmt.where(
                FindingName.product_id == product_id,
            )
        if filters:
            for k, v in filters.items():
                if not v:
                    continue
                stmt = stmt.where(getattr(Finding, k).in_(v))
        return await self.pagination(stmt, page)

    async def get_group_by_asset(
        self,
        product_id: UUID | None = None,
        filters: dict | None = None,
        page: int = 1,
    ) -> Pagination:
        stmt = (
            (
                select(
                    Finding.host,
                    func.count(case((Finding.severity == "LOW", 1))).label("low"),
                    func.count(case((Finding.severity == "MEDIUM", 1))).label("medium"),
                    func.count(case((Finding.severity == "HIGH", 1))).label("high"),
                    func.count(case((Finding.severity == "CRITICAL", 1))).label(
                        "critical"
                    ),
                    func.max(Finding.last_update).label("last_update"),
                ).join(FindingName)
            )
            .group_by(Finding.host)
            .order_by(Finding.host)
        )

        if product_id:
            stmt = stmt.where(
                FindingName.product_id == product_id,
            )

        if filters:
            for k, v in filters.items():
                if not v:
                    continue
                stmt = stmt.where(getattr(Finding, k).in_(v))

        return await self.pagination(stmt, page)

    async def get_group_by_asset_details(
        self,
        host: str,
        filters: dict | None = None,
        page: int = 1,
    ) -> Pagination:
        stmt = (
            select(Finding)
            .join(FindingName)
            .options(selectinload(Finding.finding_name).selectinload(FindingName.cves))
        ).where(Finding.host == host)
        if filters:
            for k, v in filters.items():
                if not v:
                    continue
                stmt = stmt.where(getattr(Finding, k).in_(v))
        stmt = stmt.distinct().order_by(Finding.severity, Finding.finding_date.desc())
        return await self.pagination(stmt, page, True)

    async def get_breached_findings_by_severity(
        self, product_id: UUID, severity: SeverityEnum
    ):
        sub = select(
            GlobalConfig.__table__.c[f"sla_{severity.value.lower()}"]
        ).scalar_subquery()
        today = datetime.now()
        stmt = (
            select(
                FindingName.id.label("finding_name_id"),
                FindingName.name,
                Finding.severity,
                func.max(Finding.remediation).label("remediation"),
                func.array_agg(func.distinct(Finding.host), type_=ARRAY(String)).label(
                    "hosts"
                ),
                func.extract("day", func.max(Finding.finding_date) - today).label(
                    "date"
                ),
                sub.label("sla"),
            )
            .join(FindingName)
            .where(
                FindingName.product_id == product_id,
                Finding.status.not_in([FnStatusEnum.CLOSED, FnStatusEnum.EXAMPTION]),
                Finding.severity == severity,
                func.extract("day", Finding.finding_date - today) < sub,
            )
        ).group_by(FindingName.id, FindingName.name, Finding.severity)

        query = await self.session.execute(stmt)
        return query.all()

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

    async def delete_by_filter(self, product_id: UUID, filters: dict):
        sub = (
            select(Finding.id)
            .join(FindingName)
            .where(FindingName.product_id == product_id)
        ).scalar_subquery()

        stmt = sql_delete(Finding).where(Finding.id.in_(sub))

        for k, v in filters.items():
            if not v:
                continue
            stmt = stmt.where(getattr(Finding, k).in_(v))
        await self.session.execute(stmt)
        await self.session.commit()

    async def adhoc_statitics(self, filters: dict, year: int | None = None):
        if year is None:
            ...
