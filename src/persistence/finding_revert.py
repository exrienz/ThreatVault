from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.domain.entity import Finding, FindingName, FindingRevertPoint
from src.domain.entity.finding import Log
from src.infrastructure.database import get_session
from src.persistence.base import BaseRepository


class FindingRevertRepository(BaseRepository):
    def __init__(self, session: Annotated[AsyncSession, Depends(get_session)]):
        super().__init__(FindingRevertPoint, session)

    async def get_by_product_id(self, product_id: UUID):
        stmt = (
            select(FindingRevertPoint)
            .join(FindingName)
            .where(FindingName.product_id == product_id)
        )

        query = await self.session.execute(stmt)
        return query.scalars().all()

    async def get_one_by_product_id(self, product_id: UUID):
        stmt = (
            select(FindingRevertPoint)
            .join(FindingName)
            .where(FindingName.product_id == product_id)
        )

        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def get_latest_date_by_product_id(self, product_id: UUID):
        stmt = (
            select(FindingRevertPoint.last_update)
            .join(FindingName)
            .where(FindingName.product_id == product_id)
            .order_by(FindingRevertPoint.last_update.desc())
            .limit(1)
        )

        query = await self.session.execute(stmt)
        return query.scalar()

    async def revert_point_clear(self, product_id: UUID, commit: bool = True):
        revert_point = (
            select(FindingRevertPoint)
            .join(FindingName)
            .where(FindingName.product_id == product_id)
            .cte()
        )

        alias = aliased(FindingRevertPoint, revert_point)

        cols_revert = {c.name for c in FindingRevertPoint.__table__.columns}
        cols_finding = {c.name for c in Finding.__table__.columns}
        cols = cols_finding.intersection(cols_revert)

        dct = {getattr(Finding, attr): getattr(alias, attr) for attr in cols}

        stmt = (
            update(Finding)
            .values(dct)
            .where(Finding.id == alias.id)
            .add_cte(revert_point)
        )

        await self.session.execute(stmt)
        if commit:
            await self.session.commit()

    async def revert(self, product_id: UUID):
        await self.revert_point_clear(product_id, False)
        # Revert logs
        sub = (
            select(Log.id)
            .where(Log.product_id == product_id)
            .limit(1)
            .order_by(Log.created_at.desc())
        ).subquery()

        delete_stmt = delete(Log).where(Log.id == sub.c.id)
        await self.session.execute(delete_stmt)

        await self.session.commit()

    @classmethod
    async def create_revert_point(cls, session: AsyncSession, product_id: UUID):
        cols = [c.name for c in FindingRevertPoint.__table__.columns]

        old_cols = [getattr(Finding, attr) for attr in cols]

        old_findings = (
            select(*old_cols)
            .join(FindingName)
            .where(FindingName.product_id == product_id)
            .cte()
        )

        subquery = (
            select(FindingRevertPoint.id)
            .join(FindingName)
            .where(FindingName.product_id == product_id)
        ).subquery()

        delete_stmt = delete(FindingRevertPoint).where(
            FindingRevertPoint.id == subquery.columns.id
        )
        await session.execute(delete_stmt)
        stmt = insert(FindingRevertPoint).from_select(cols, old_findings)
        await session.execute(stmt)
        await session.commit()
