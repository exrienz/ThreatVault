from datetime import datetime
from uuid import UUID

import polars as pl
import pytz
from fastapi import Depends
from sqlalchemy import Float, Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entity import Environment, Finding, FindingName, Log, Product, Project
from src.infrastructure.database import sync_engine
from src.infrastructure.database.session import get_session
from src.persistence.base import BaseRepository


class LogRepository(BaseRepository[Log]):
    def __init__(self, session: AsyncSession = Depends(get_session)):
        super().__init__(Log, session)

    async def calculate(
        self,
        product_id: UUID,
        uploader_id: UUID,
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
        log_data["uploader_id"] = uploader_id
        return await self.create(log_data)

    async def get_by_product_id(self, product_id: UUID):
        subquery = (
            select(func.max(Log.log_date).label("log_date"))
            .group_by(Log.product_id)
            .having(Log.product_id == product_id)
            .subquery()
        )
        stmt = (
            select(Log)
            .options(selectinload(Log.uploader))
            .where(
                Log.product_id == product_id, Log.log_date == subquery.columns.log_date
            )
        )

        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def get_products_by_env(self, env_id: UUID, year: int, month: int):
        sub = (
            select(
                Log,
                func.extract("year", Log.log_date).label("year"),
                func.extract("month", Log.log_date).label("month"),
                func.row_number()
                .over(
                    order_by=[Log.log_date.desc()],
                    partition_by=[
                        Log.product_id,
                        func.extract("year", Log.log_date),
                        func.extract("month", Log.log_date),
                    ],
                )
                .label("rank"),
            )
        ).alias()
        stmt = (
            select(sub)
            .join(Product)
            .where(
                sub.c.rank == 1,
                Product.environment_id == env_id,
                sub.c.year == year,
                sub.c.month == month,
            )
        )
        query = await self.session.execute(stmt)
        return query.all()

    async def get_project_list(self):
        sub = (
            select(
                Log,
                func.extract("year", Log.log_date).label("year"),
                func.extract("month", Log.log_date).label("month"),
                func.row_number()
                .over(
                    order_by=[Log.log_date.desc()],
                    partition_by=[Log.product_id],
                )
                .label("rank"),
            )
        ).alias()
        t_new = func.sum(sub.c.tNew)
        t_open = func.sum(sub.c.tOpen)
        t_exemption = func.sum(sub.c.tExamption)
        t_closed = func.sum(sub.c.tClosed)
        t_others = func.sum(sub.c.tOthers)

        total = t_new + t_open + t_exemption + t_closed + t_others
        slct = [
            Project.id,
            Project.name,
            t_new,
            t_open,
            t_exemption,
            t_closed,
            t_others,
            func.cast(
                ((func.cast(t_closed, Float) / func.cast(total, Float)) * 100), Integer
            ).label("complete_percentage"),
        ]
        stmt = (
            select(*slct)
            .join(Product, sub.c.product_id == Product.id)
            .join(Environment, Product.environment_id == Environment.id)
            .join(Project, Environment.project_id == Project.id)
            .where(
                sub.c.rank == 1,
            )
            .group_by(Project.id, Project.name)
        )
        query = await self.session.execute(stmt)
        return query.all()

    def _statistics(self, partition=Log.product_id):
        stmt = select(
            Log,
            Product.name.label("product_name"),
            Product.environment_id.label("environment_id"),
            func.extract("month", Log.log_date).label("month"),
            func.row_number()
            .over(
                order_by=[Log.log_date.desc()],
                partition_by=[
                    partition,
                    func.extract("year", Log.log_date),
                    func.extract("month", Log.log_date),
                ],
            )
            .label("rank"),
        )
        stmt = stmt.join(Product).alias()
        return stmt

    async def statistics(self, product_id: UUID, year: int | None = None):
        if year is None:
            year = datetime.now().year
        sub = self._statistics()

        stmt = select(sub).where(
            sub.c.rank == 1,
            sub.c.product_id == product_id,
            func.extract("year", sub.c.log_date) == year,
        )
        query = await self.session.execute(stmt)
        return query.all()

    async def statistics_by_environment(
        self, env_id: UUID, year: int | None = None, month: int | None = None
    ):
        if year is None:
            year = datetime.now().year
        sub = self._statistics()
        slct = (
            sub.c.environment_id,
            sub.c.month,
            func.sum(sub.c.tCritical).label("tCritical"),
            func.sum(sub.c.tHigh).label("tHigh"),
            func.sum(sub.c.tMedium).label("tMedium"),
            func.sum(sub.c.tLow).label("tLow"),
        )
        stmt = (
            select(*slct)
            .where(
                sub.c.rank == 1,
                func.extract("year", sub.c.log_date) == year,
                sub.c.environment_id == env_id,
            )
            .group_by(sub.c.environment_id, sub.c.month, sub.c.rank)
        )

        if month:
            stmt = stmt.where(sub.c.month == month)
        query = await self.session.execute(stmt)
        return query.all()

    async def get_date_options_by_env(self, env_id: UUID):
        stmt = (
            select(
                func.extract("year", Log.log_date).label("year"),
                func.extract("month", Log.log_date).label("month"),
            )
            .distinct()
            .join(Product)
            .where(Product.environment_id == env_id)
            .order_by(
                func.extract("year", Log.log_date).label("year").desc(),
                func.extract("month", Log.log_date).label("month").desc(),
            )
        )
        query = await self.session.execute(stmt)
        return query.all()
