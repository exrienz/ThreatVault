from collections.abc import Sequence
from datetime import datetime
from math import ceil
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from pydantic import BaseModel, NonNegativeInt, PositiveInt
from sqlalchemy import ARRAY, Select, String, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.constant import FnStatusEnum
from src.domain.entity import Finding, FindingName
from src.infrastructure.database.session import get_session


class Pagination(BaseModel):
    total: NonNegativeInt
    size: NonNegativeInt
    page: NonNegativeInt
    total_page: NonNegativeInt
    data: Sequence


class FindingRepository:
    def __init__(self, session: Annotated[AsyncSession, Depends(get_session)]):
        self.session = session

    async def get_by_filter(
        self,
        scan_date: datetime | None = None,
    ) -> Finding | None:
        stmt = select(Finding)
        if scan_date:
            stmt = stmt.where(Finding.finding_date > scan_date)
        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def get(self, item_id: UUID):
        stmt = (
            select(Finding)
            .options(selectinload(Finding.finding_name))
            .where(Finding.id == item_id)
        )

        query = await self.session.execute(stmt)
        return query.scalars().all()

    async def pagination(self, stmt: Select, page: PositiveInt, scalars: bool = False):
        limit = 25
        fn_stmt = stmt.limit(limit).offset((page - 1) * limit)
        query = await self.session.execute(fn_stmt)
        if scalars:
            findings = query.scalars().all()
        else:
            findings = query.all()

        addition_query = stmt.with_only_columns(func.count().label("total"))
        query = await self.session.execute(addition_query.order_by(None))
        total = query.scalar() or 0

        return Pagination(
            total=total,
            size=limit,
            page=page,
            total_page=ceil(total / limit),
            data=findings,
        )

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

    async def get_group_by_severity_status(
        self,
        product_id: UUID,
        page: int = 1,
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
            .group_by(FindingName.id, Finding.severity, Finding.status)
        ).order_by(Finding.severity)
        return await self.pagination(stmt, page)

    async def update(self, item_id: UUID, hosts: list, data: dict):
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
