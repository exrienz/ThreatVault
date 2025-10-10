from datetime import datetime
from typing import Annotated
from uuid import UUID

import polars as pl
import pytz
from fastapi import Depends
from sqlalchemy import (
    Float,
    Integer,
    Row,
    Select,
    Subquery,
    and_,
    case,
    cast,
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.constant import FnStatusEnum, HAStatusEnum, SeverityEnum, VAStatusEnum
from src.domain.entity import Environment, Finding, FindingName, Log, Product, Project
from src.domain.entity.setting import GlobalConfig
from src.infrastructure.database import sync_engine
from src.infrastructure.database.session import get_session
from src.persistence.base import BaseRepository
from src.presentation.dependencies import (
    get_allowed_product_ids,
    get_allowed_project_ids,
)


class LogRepository(BaseRepository[Log]):
    # TYPE_MAP = {
    #     "severity": ["Critical", "High", "Medium", "Low"],
    #     "status": ["New", "Open", "Closed", "Exemption", "Others"],
    #     "status_va": ["New", "Open", "Closed", "Exemption", "Others"],
    #     "status_ha": ["Passed", "Warning", "Failed"],
    # }

    TYPE_MAP = {
        "severity": ["Critical", "High", "Medium", "Low"],
        "status": {
            "va": ["New", "Open", "Closed", "Exemption", "Others"],
            "ha": ["Passed", "Warning", "Failed"],
        },
        "status_va": ["New", "Open", "Closed", "Exemption", "Others"],
        "status_ha": ["Passed", "Warning", "Failed"],
    }

    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(get_session)],
        project_ids: Annotated[list[UUID], Depends(get_allowed_project_ids)],
        product_ids: Annotated[list[UUID], Depends(get_allowed_product_ids)],
    ):
        super().__init__(Log, session, project_ids, product_ids)

    async def calculate(
        self,
        product_id: UUID,
        uploader_id: UUID,
        scan_date: datetime = datetime(2025, 1, 1, 0, 0, 0, 0, pytz.utc),
    ):
        stmt = (
            select(Project)
            .join(Environment)
            .join(Product)
            .where(Product.id == product_id)
        )

        query = await self.session.execute(stmt)
        project = query.scalar_one()
        if project.type_ == "HA":
            return await self.calculate_ha(product_id, uploader_id, scan_date)
        return await self.calculate_va(product_id, uploader_id, scan_date)

    # TODO: Generalize this back
    async def calculate_va(
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
            .group_by(Finding.status)
            .where(Finding.product_id == product_id)
        )
        status_calc = pl.read_database(status_stmt, connection=sync_engine).lazy()
        print("status calc")
        print(status_calc.collect())

        severity_stmt = (
            select(
                Finding.severity.label("value"),
                func.count(Finding.id).label("total"),
            )
            .join(FindingName)
            .group_by(Finding.severity)
            .where(
                Finding.product_id == product_id,
                Finding.status.not_in(
                    [
                        VAStatusEnum.CLOSED.value,
                        VAStatusEnum.OTHERS.value,
                        VAStatusEnum.EXEMPTION.value,
                    ]
                ),
                # Finding.last_update == scan_date,
            )
        )

        severity_calc = pl.read_database(severity_stmt, connection=sync_engine).lazy()
        severity_calc = severity_calc.with_columns(
            pl.col("value").map_elements(lambda x: x.value, return_dtype=pl.String)
        )
        combined_df = pl.concat([status_calc, severity_calc], how="vertical")

        dct = (
            combined_df.with_columns(
                pl.col("value").map_elements(
                    lambda x: "t" + x.title(), return_dtype=pl.String
                )
            )
            .collect()
            .to_dict(as_series=False)
        )
        log_data = {k: v for k, v in zip(dct["value"], dct["total"])}
        log_data["product_id"] = product_id
        log_data["log_date"] = scan_date
        log_data["uploader_id"] = uploader_id
        sla_breach = await self.calculate_breach(product_id, scan_date)
        log_data.update(sla_breach)
        log_data["score"] = await self.calculate_score_simple(product_id)
        return await self.create(log_data)

    async def calculate_ha(
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
            .group_by(Finding.status)
            .where(Finding.product_id == product_id)
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
                Finding.product_id == product_id,
                Finding.status != HAStatusEnum.PASSED.value,
                # Finding.last_update == scan_date,
            )
        )

        severity_calc = pl.read_database(severity_stmt, connection=sync_engine).lazy()
        severity_calc = severity_calc.with_columns(
            pl.col("value").map_elements(lambda x: x.value, return_dtype=pl.String)
        )
        combined_df = pl.concat([status_calc, severity_calc], how="vertical")

        dct = (
            combined_df.with_columns(
                pl.col("value").map_elements(
                    lambda x: "t" + x.title(), return_dtype=pl.String
                )
            )
            .collect()
            .to_dict(as_series=False)
        )
        log_data = {k: v for k, v in zip(dct["value"], dct["total"])}
        log_data["product_id"] = product_id
        log_data["log_date"] = scan_date
        log_data["uploader_id"] = uploader_id
        sla_breach = await self.calculate_breach(product_id, scan_date)
        log_data.update(sla_breach)
        log_data["score"] = await self.calculate_score_simple(product_id)
        return await self.create(log_data)

    async def calculate_breach(self, product_id: UUID, scan_date: datetime) -> dict:
        status_excludes = ["CLOSED", "OTHERS", "PASSED", "EXEMPTION"]

        sub = select(
            GlobalConfig.sla_critical.label("CRITICAL"),
            GlobalConfig.sla_high.label("HIGH"),
            GlobalConfig.sla_medium.label("MEDIUM"),
            GlobalConfig.sla_low.label("LOW"),
        ).subquery()

        sla_count = []

        for status in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            sub_c_status = getattr(sub.c, status)
            sub_stmt = func.count(
                case(
                    (
                        and_(
                            Finding.severity == status,
                            func.date_part("day", scan_date - Finding.finding_date)
                            > sub_c_status,
                            Finding.status.not_in(status_excludes),
                        ),
                        1,
                    )
                )
            ).label(f"b{status.title()}")
            sla_count.append(sub_stmt)
        stmt = (
            select(
                *sla_count,
            )
            .select_from(Finding)
            .join(FindingName)
        ).where(Finding.product_id == product_id)
        query = await self.session.execute(stmt)
        data = query.one_or_none()
        if data:
            return data._asdict()
        return {}

    async def calculate_score_simple(self, product_id: UUID):
        stmt = (
            select(Finding.severity, func.count(1))
            .where(
                Finding.product_id == product_id,
                Finding.status.not_in(
                    [
                        FnStatusEnum.CLOSED.value,
                        FnStatusEnum.OTHERS.value,
                        FnStatusEnum.EXEMPTION.value,
                    ]
                ),
            )
            .group_by(Finding.severity)
        )
        query = await self.session.execute(stmt)
        res = query.all()
        res_dict = {}
        for r in res:
            res_dict[r[0]] = r[1]

        CRITICAL = res_dict.get(SeverityEnum.CRITICAL, 0)
        HIGH = res_dict.get(SeverityEnum.HIGH, 0)
        MEDIUM = res_dict.get(SeverityEnum.MEDIUM, 0)
        LOW = res_dict.get(SeverityEnum.LOW, 0)

        if CRITICAL > 10:
            return 4
        if CRITICAL > 0 or HIGH > 20:
            return 3
        if HIGH > 0 or MEDIUM > 30:
            return 2
        if MEDIUM > 0 or LOW > 40:
            return 1
        return 0

    async def get_by_product_id(self, product_id: UUID) -> Log:
        await self.calculate_score_simple(product_id)
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
            .order_by(Log.created_at.desc())
        )

        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def get_prev_by_product_id(self, product_id: UUID):
        sub = (
            select(
                Log.id.label("id"),
                func.row_number()
                .over(order_by=[Log.log_date.desc()], partition_by=[Log.product_id])
                .label("rank"),
            )
            .where(Log.product_id == product_id)
            .alias()
        )

        stmt = (
            select(Log)
            .join(sub, sub.c.id == Log.id)
            .where(
                sub.c.rank == 2,
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
        stmt = self._product_allowed_ids(stmt)
        query = await self.session.execute(stmt)
        return query.all()

    async def get_latest_available_date(self, env_id: UUID, year: int, month: int):
        s_month = cast(func.extract("month", Log.log_date), Integer).label("month")
        s_year = cast(func.extract("year", Log.log_date), Integer).label("year")

        stmt = (
            select(s_month, s_year)
            .join(Product)
            .where(Product.environment_id == env_id, s_month <= month, s_year <= year)
            .order_by(Log.created_at.desc())
            .limit(1)
        )
        query = await self.session.execute(stmt)
        return query.first()

    def _select_project_list_va(self, sub: Subquery):
        t_new = func.sum(sub.c.tNew)
        t_open = func.sum(sub.c.tOpen)
        t_exemption = func.sum(sub.c.tExemption)
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
        return slct

    def _select_project_list_ha(self, sub: Subquery):
        t_passed = func.sum(sub.c.tPassed)
        t_warning = func.sum(sub.c.tWarning)
        t_failed = func.sum(sub.c.tFailed)

        total = t_passed + t_warning + t_failed
        slct = [
            Project.id,
            Project.name,
            t_passed,
            t_warning,
            t_failed,
            func.cast(
                ((func.cast(t_passed, Float) / func.cast(total, Float)) * 100), Integer
            ).label("complete_percentage"),
        ]
        return slct

    async def get_project_list(self, env: str | None = None):
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
        if env == "HA":
            slct = self._select_project_list_ha(sub)
        else:
            slct = self._select_project_list_va(sub)
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

        if env:
            stmt = stmt.where(Project.type_ == env)
        stmt = self._product_allowed_ids(stmt)
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

    async def _get_statistics_labels(
        self,
        type_: str = "severity",
        project_id: UUID | None = None,
        env_id: UUID | None = None,
        product_id: UUID | None = None,
    ) -> list:
        if type_ == "severity":
            return self.TYPE_MAP.get("severity", [])
        stmt = select(Project.type_)
        if project_id:
            stmt = stmt.where(Project.id == project_id)
        elif env_id:
            stmt = stmt.join(Environment).where(Environment.id == env_id)
        elif product_id:
            stmt = stmt.join(Environment).join(Product).where(Product.id == product_id)
        else:
            raise NotImplementedError
        query = await self.session.execute(stmt)
        project_type = query.scalar_one()
        return self.TYPE_MAP.get("status", {}).get(project_type.lower(), [])

    async def statistics_by_environment(
        self,
        project_id: UUID | None = None,
        env_id: UUID | None = None,
        year: int | None = None,
        month: int | None = None,
        type_: str = "severity",
    ):
        if year is None:
            year = datetime.now().year
        sub = self._statistics()

        labels = await self._get_statistics_labels(
            type_, project_id=project_id, env_id=env_id
        )

        if labels is None:
            raise NotImplementedError

        query_lst = [
            func.sum(getattr(sub.c, f"t{label.title()}")).label(label)
            for label in labels
        ]

        # month_cte = select(func.generate_series(1, 12).label("month")).cte("months")
        slct = (
            sub.c.environment_id,
            sub.c.month,
            *query_lst,
        )
        stmt = (
            select(*slct)
            .where(
                sub.c.rank == 1,
                func.extract("year", sub.c.log_date) == year,
            )
            .group_by(sub.c.environment_id, sub.c.month, sub.c.rank)
        ).join(Product, sub.c.product_id == Product.id)

        if project_id:
            stmt = stmt.join(Environment, sub.c.environment_id == Environment.id).where(
                Environment.project_id == project_id
            )
        elif env_id:
            stmt = stmt.where(sub.c.environment_id == env_id)

        stmt = self._product_allowed_ids(stmt)

        if month:
            stmt = stmt.where(sub.c.month == month)

        # data_cte = stmt.cte()

        # stmt = select(
        #     data_cte.c.environment_id,
        #     month_cte.c.month,
        #     func.coalesce(data_cte.c.total,
        #                   func.lag(data_cte.c.total)
        # )
        query = await self.session.execute(stmt)
        return query.all()

    async def get_date_options(
        self, env_id: UUID | None = None, product_id: UUID | None = None
    ):
        stmt = (
            select(
                func.extract("year", Log.log_date).label("year"),
                func.extract("month", Log.log_date).label("month"),
            )
            .distinct()
            .order_by(
                func.extract("year", Log.log_date).label("year").desc(),
                func.extract("month", Log.log_date).label("month").desc(),
            )
        )
        if env_id:
            stmt = stmt.join(Product)
            stmt = stmt.where(Product.environment_id == env_id)

        if product_id:
            stmt = stmt.where(Log.product_id == product_id)
        query = await self.session.execute(stmt)
        return query.all()

    async def get_first_date(
        self, env_id: UUID | None = None, product_id: UUID | None = None
    ):
        stmt = (
            select(
                cast(func.extract("year", Log.log_date), Integer).label("year"),
                cast(func.extract("month", Log.log_date), Integer).label("month"),
            )
            .order_by(Log.log_date)
            .limit(1)
        )
        if env_id:
            stmt = stmt.join(Product)
            stmt = stmt.where(Product.environment_id == env_id)

        if product_id:
            stmt = stmt.where(Log.product_id == product_id)
        query = await self.session.execute(stmt)
        return query.first()

    async def compare_stats(self, filters: dict):
        product_ids: list[UUID] = filters.get("product_ids", [])
        curr_date: datetime = filters.get("curr_date", datetime.now())

        subquery = (
            select(Log)
            .where(func.extract("month", Log.log_date) == curr_date.month - 1)
            .subquery()
        )
        stmt = select(
            Log.product_id, Log.tClosed - func.coalesce(subquery.c.tClosed)
        ).where(
            Log.product_id.in_(product_ids),
            func.extract("month", Log.log_date) == curr_date.month,
        )

        query = await self.session.execute(stmt)
        return query.all()

    def _project_allowed_ids(self, stmt: Select) -> Select:
        if self.allowed_project_ids is None:
            return stmt
        return stmt.where(Project.id.in_(self.allowed_project_ids))

    def _product_allowed_ids(self, stmt: Select) -> Select:
        if self.allowed_product_ids is None:
            return stmt
        return stmt.where(Product.id.in_(self.allowed_product_ids))

    async def get_by_project_id(
        self,
        project_id: UUID,
        year: int | None = None,
        month: int | None = None,
        page: int = 1,
    ):
        today = datetime.now()
        if year is None:
            year = today.year
        if month is None:
            month = today.month

        sub = self._statistics()

        sub_product_ids = (
            select(Product.id)
            .join(Environment)
            .where(Environment.project_id == project_id)
        )

        stmt = select(sub).where(
            sub.c.rank == 1,
            sub.c.product_id.in_(sub_product_ids),
            func.extract("year", sub.c.log_date) == year,
            func.extract("month", sub.c.log_date) == month,
        )
        return await self.pagination(stmt, page)

    async def get_total_by_project_id(
        self,
        project_id: UUID,
        filters: dict,
        year: int | None = None,
        month: int | None = None,
    ) -> Row:
        today = datetime.now()
        if year is None:
            year = today.year
        if month is None:
            month = today.month

        sub = self._statistics()

        sub_product_ids = (
            select(Product.id)
            .join(Environment)
            .where(Environment.project_id == project_id)
        )

        if env_name := filters.get("env_type"):
            sub_product_ids = sub_product_ids.where(Environment.name == env_name)

        if filters.get("type") == "breach":
            sum_status = [
                func.sum(sub.c.bCritical).label("CRITICAL"),
                func.sum(sub.c.bHigh).label("HIGH"),
                func.sum(sub.c.bMedium).label("MEDIUM"),
                func.sum(sub.c.bLow).label("LOW"),
            ]
        else:
            sum_status = [
                func.sum(sub.c.tCritical).label("CRITICAL"),
                func.sum(sub.c.tHigh).label("HIGH"),
                func.sum(sub.c.tMedium).label("MEDIUM"),
                func.sum(sub.c.tLow).label("LOW"),
            ]
        stmt = select(*sum_status).where(
            sub.c.rank == 1,
            sub.c.product_id.in_(sub_product_ids),
            func.extract("year", sub.c.log_date) == year,
            func.extract("month", sub.c.log_date) == month,
        )

        query = await self.session.execute(stmt)
        return query.one()

    async def get_yearly_log_by_product_ids(
        self, product_id: list[UUID], year: int | None
    ):
        if year is None:
            year = datetime.now().year

        sub = self._statistics()

        stmt = (
            select(sub)
            .where(
                sub.c.rank == 1,
                sub.c.product_id.in_(product_id),
                func.extract("year", sub.c.log_date) == year,
            )
            .order_by(sub.c.month)
        )

        query = await self.session.execute(stmt)
        return query.all()

    async def get_yearly_log_by_env_id(self, env_id: UUID, year: int | None):
        if year is None:
            year = datetime.now().year

        sub = self._statistics()

        stmt = (
            select(sub)
            .where(
                sub.c.rank == 1,
                sub.c.environment_id == env_id,
                func.extract("year", sub.c.log_date) == year,
            )
            .order_by(sub.c.month, sub.c.product_name)
        )

        query = await self.session.execute(stmt)
        return query.all()

    async def get_by_date_filter(self, product_id: UUID, year: int, month: int):
        stmt = (
            select(Log)
            .where(
                Log.product_id == product_id,
                func.extract("year", Log.log_date) == year,
                func.extract("month", Log.log_date) == month,
            )
            .order_by(Log.log_date.desc())
        )
        query = await self.session.execute(stmt)
        return query.scalars().first()
