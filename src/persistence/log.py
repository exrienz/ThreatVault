from datetime import datetime
from uuid import UUID

import polars as pl
import pytz
from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity import Finding, FindingName, Log
from src.infrastructure.database import sync_engine
from src.infrastructure.database.session import get_session


class LogRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session

    async def calculate(
        self,
        product_id: UUID,
        scan_date: datetime = datetime(2025, 1, 1, 0, 0, 0, 0, pytz.utc),
    ):
        status_stmt = (
            select(
                Finding.status.label("value"),
                func.count(Finding.id).label("total"),
            )
            .join(FindingName)
            .group_by(Finding.status)
            .where(
                FindingName.product_id == product_id,
                Finding.last_update == scan_date,
            )
        )
        status_calc = pl.read_database(status_stmt, connection=sync_engine).lazy()

        severity_stmt = (
            select(
                Finding.severity.label("value"),
                func.count(Finding.id).label("total"),
            )
            .join(FindingName)
            .group_by(Finding.severity)
            .where(
                FindingName.product_id == product_id,
                Finding.last_update == scan_date,
            )
        )

        severity_calc = pl.read_database(severity_stmt, connection=sync_engine).lazy()

        combined_df = pl.concat([status_calc, severity_calc], how="vertical")

        dct = (
            combined_df.with_columns(
                pl.col("value").map_elements(
                    lambda x: "t" + x.value.title(), return_dtype=pl.String
                )
            )
            .collect()
            .to_dict(as_series=False)
        )

        log_data = {k: v for k, v in zip(dct["value"], dct["total"])}
        log_data["product_id"] = product_id
        log_data["log_date"] = scan_date
        return await self.create(log_data)

    async def create(self, data: dict):
        db_data = Log(**data)
        self.session.add(db_data)
        await self.session.commit()
        await self.session.refresh(db_data)
        return db_data

    async def get_by_product_id(self, product_id: UUID):
        subquery = (
            select(func.max(Log.log_date).label("log_date"))
            .group_by(Log.product_id)
            .having(Log.product_id == product_id)
            .subquery()
        )
        stmt = select(Log).where(
            Log.product_id == product_id, Log.log_date == subquery.columns.log_date
        )

        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def statistics(self, product_id: UUID, year: int | None = None):
        if year is None:
            year = datetime.now().year
        sub = select(
            Log,
            func.extract("month", Log.log_date).label("month"),
            func.row_number()
            .over(
                order_by=[Log.product_id, Log.log_date.desc()],
                partition_by=[
                    func.extract("year", Log.log_date),
                    func.extract("month", Log.log_date),
                ],
            )
            .label("rank"),
        ).alias()
        stmt = select(sub).where(
            sub.c.rank == 1,
            sub.c.product_id == product_id,
            func.extract("year", sub.c.log_date) == year,
        )
        query = await self.session.execute(stmt)
        return query.all()
