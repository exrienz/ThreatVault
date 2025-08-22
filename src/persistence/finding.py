from collections.abc import Sequence
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import (
    ARRAY,
    Select,
    String,
    and_,
    case,
    cast,
    func,
    or_,
    select,
    update,
)
from sqlalchemy import (
    UUID as SQL_UUID,
)
from sqlalchemy import (
    delete as sql_delete,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.constant import FnStatusEnum, HAStatusEnum, SeverityEnum
from src.domain.entity import Finding, FindingName
from src.domain.entity.finding import CVE
from src.domain.entity.project_management import Environment, Product, Project
from src.domain.entity.setting import GlobalConfig
from src.infrastructure.database import get_session
from src.persistence.base import BaseRepository, Pagination


class FindingRepository(BaseRepository[Finding]):
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
        filters = {"product_id": product_id}
        return await self.get_all_by_filter(
            filters=filters, order_by=["severity"], pagination=pagination, page=page
        )

    async def get_latest_date_by_product_id(self, product_id: UUID):
        stmt = (
            select(Finding.last_update)
            .where(Finding.product_id == product_id)
            .order_by(Finding.last_update.desc())
            .limit(1)
        )

        query = await self.session.execute(stmt)
        return query.scalar()

    async def get_all_by_project_id(self, project_id: UUID) -> Sequence[Finding]:
        stmt = (select(Finding).join(Product).join(Environment).join(Project)).where(
            Project.id == project_id
        )

        stmt = stmt.options(
            selectinload(Finding.finding_name)
            .selectinload(Finding.product)
            .selectinload(Product.environment)
        )

        query = await self.session.execute(stmt)
        return query.scalars().all()

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
                    Finding.remark,
                    # func.max(Finding.remark).label("remark"),
                    func.max(Finding.finding_date),
                    func.array_agg(
                        func.distinct(Finding.plugin_id), type_=ARRAY(SQL_UUID)
                    ).label("plugin_ids"),
                    func.array_agg(
                        func.distinct(Finding.host), type_=ARRAY(String)
                    ).label("hosts"),
                ).join(FindingName)
            )
            .group_by(FindingName.id, Finding.severity, Finding.status, Finding.remark)
            .order_by(Finding.severity)
        )
        if product_id:
            stmt = stmt.where(
                Finding.product_id == product_id,
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
                Finding.product_id == product_id,
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

    async def get_status_group_by_products(self, filters: dict, page: int = 1):
        stmt = (
            select(
                Product.id,
                Product.name,
                Environment.name,
                func.count(case((Finding.status == FnStatusEnum.OPEN, 1))).label(
                    "Open"
                ),
                func.count(case((Finding.status == FnStatusEnum.NEW, 1))).label("New"),
                func.count(case((Finding.status == FnStatusEnum.CLOSED, 1))).label(
                    "Closed"
                ),
                func.count(case((Finding.status == FnStatusEnum.EXEMPTION, 1))).label(
                    "Exemption"
                ),
                func.count(case((Finding.status == FnStatusEnum.OTHERS, 1))).label(
                    "Others"
                ),
            )
            .select_from(Finding)
            .join(FindingName)
            .join(Product)
            .join(Environment)
        ).group_by(Product.id, Product.name, Environment.name)

        if project_id := filters.get("project_id"):
            stmt = stmt.where(Project.id == project_id)

        if product_ids := filters.get("product_ids"):
            stmt = stmt.where(Product.id.in_(product_ids))

        return await self.pagination(stmt, page)

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
                Finding.product_id == product_id,
                Finding.status.not_in([FnStatusEnum.CLOSED, FnStatusEnum.EXEMPTION]),
                Finding.severity == severity,
                func.extract("day", Finding.finding_date - today) < sub,
            )
        ).group_by(FindingName.id, FindingName.name, Finding.severity)

        query = await self.session.execute(stmt)
        return query.all()

    async def get_breached_findings_by_severity_filters(self, filters: dict):
        """
        Filters:
            severity: str [Optional] = "CRITICAL"
            product_id: UUID | str [Optional]
            project_id: UUID | str [Optional]
        """
        severity = filters.get("severity", "CRITICAL")
        sub = select(
            GlobalConfig.__table__.c[f"sla_{severity.lower()}"]
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
                Finding.status.not_in([FnStatusEnum.CLOSED, FnStatusEnum.EXEMPTION]),
                Finding.severity == severity,
                func.extract("day", Finding.finding_date - today) < sub,
            )
        ).group_by(FindingName.id, FindingName.name, Finding.severity)

        if product_id := filters.get("product_id"):
            stmt = stmt.where(Finding.product_id == product_id)

        if project_id := filters.get("project_id"):
            stmt = stmt.join(Environment)
            stmt = stmt.where(Environment.project_id == project_id)

        query = await self.session.execute(stmt)
        return query.all()

    # Deprecated
    async def get_sla_breach_for_rtf(
        self,
        project_id: UUID,
        severities: list[str],
        status_excludes: list[str],
        page: int = 1,
    ) -> Pagination:
        sub = select(
            GlobalConfig.sla_critical.label("CRITICAL"),
            GlobalConfig.sla_high.label("HIGH"),
            GlobalConfig.sla_medium.label("MEDIUM"),
            GlobalConfig.sla_low.label("LOW"),
        ).subquery()

        today = datetime.now()

        sla_case = case(
            (
                and_(
                    Finding.severity == "CRITICAL",
                    func.date_part("day", today - Finding.finding_date)
                    > sub.c.CRITICAL,
                    Finding.status.not_in(status_excludes),
                ),
                1,
            ),
            (
                and_(
                    Finding.severity == "HIGH",
                    func.date_part("day", today - Finding.finding_date) > sub.c.HIGH,
                    Finding.status.not_in(status_excludes),
                ),
                1,
            ),
            (
                and_(
                    Finding.severity == "MEDIUM",
                    func.date_part("day", today - Finding.finding_date) > sub.c.MEDIUM,
                    Finding.status.not_in(status_excludes),
                ),
                1,
            ),
            (
                and_(
                    Finding.severity == "LOW",
                    func.date_part("day", today - Finding.finding_date) > sub.c.LOW,
                    Finding.status.not_in(status_excludes),
                ),
                1,
            ),
            else_=0,
        )

        status_count = [
            func.count(case((Finding.status == FnStatusEnum.OPEN, 1))).label("Open"),
            func.count(case((Finding.status == FnStatusEnum.NEW, 1))).label("New"),
            func.count(case((Finding.status == FnStatusEnum.CLOSED, 1))).label(
                "Closed"
            ),
            func.count(case((Finding.status == FnStatusEnum.EXEMPTION, 1))).label(
                "Exemption"
            ),
            func.count(case((Finding.status == FnStatusEnum.OTHERS, 1))).label(
                "Others"
            ),
        ]

        stmt = (
            (
                select(
                    Product.id.label("product_id").cast(String),
                    Product.name.label("product_name"),
                    Environment.name.label("environment_name"),
                    func.sum(sla_case).label("sla_count"),
                    *status_count,
                )
                .select_from(Finding)
                .join(FindingName)
                .join(Product)
                .join(Environment)
            )
            .where(
                Environment.project_id == project_id,
            )
            .group_by(Product.id, Product.name, Environment.name)
        )

        if severities:
            stmt = stmt.where(Finding.severity.in_(severities))
        return await self.pagination(stmt, page)

    async def get_sla_breach_status(self, project_id: UUID, filters: dict):
        sub = select(
            GlobalConfig.sla_critical.label("CRITICAL"),
            GlobalConfig.sla_high.label("HIGH"),
            GlobalConfig.sla_medium.label("MEDIUM"),
            GlobalConfig.sla_low.label("LOW"),
        ).subquery()

        today = datetime.now()
        sla_count = []
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            sub_stmt = func.count(
                case(
                    (
                        and_(
                            Finding.severity == severity,
                            func.date_part("day", today - Finding.finding_date)
                            > getattr(sub.c, severity),
                        ),
                        1,
                    )
                )
            ).label(severity)
            sla_count.append(sub_stmt)

        stmt = (
            (
                select(
                    Product.id.label("product_id").cast(String),
                    Product.name.label("product_name"),
                    Environment.name.label("environment_name"),
                    *sla_count,
                )
                .select_from(Finding)
                .join(FindingName)
                .join(Product)
                .join(Environment)
            )
            .where(Environment.project_id == project_id)
            .group_by(Product.id, Product.name, Environment.name)
        )

        if env := filters.get("env"):
            stmt = stmt.where(Environment.name == env)

        query = await self.session.execute(stmt)
        return query.all()

    async def update(self, item_id: UUID, filters: dict, data: dict):
        stmt = (
            update(Finding)
            .where(
                Finding.finding_name_id == item_id,
                or_(
                    Finding.status != FnStatusEnum.CLOSED.value,
                    Finding.status != HAStatusEnum.PASSED.value,
                ),
            )
            .values(data)
        )
        if hosts := filters.get("hosts"):
            stmt = stmt.where(Finding.host.in_(hosts))
        if c_status := filters.get("current_status"):
            stmt = stmt.where(Finding.status == c_status)
        await self.session.execute(stmt)
        await self.session.commit()

    async def bulk_update(self, filters: dict, data: dict):
        stmt = (
            update(Finding)
            .where(
                Finding.status != FnStatusEnum.CLOSED,
            )
            .values(data)
        )
        stmt = self._filters(stmt, filters)
        await self.session.execute(stmt)
        await self.session.commit()

    async def delete_by_filter(self, product_id: UUID, filters: dict):
        sub = (
            select(Finding.id).join(FindingName).where(Finding.product_id == product_id)
        ).scalar_subquery()

        stmt = sql_delete(Finding).where(Finding.id.in_(sub))

        for k, v in filters.items():
            if not v:
                continue
            stmt = stmt.where(getattr(Finding, k).in_(v))
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_by_priority_list(
        self, project_id: UUID, priorities: list[str], filters: dict, page: int = 1
    ):
        stmt = (
            select(
                FindingName.name.label("finding_name"),
                func.array_agg(
                    func.distinct(
                        case(
                            (Finding.port.is_(None), Finding.host),
                            else_=func.concat(
                                Finding.host, ":", cast(Finding.port, String)
                            ),
                        )
                    )
                ).label("hosts"),
                func.array_agg(
                    func.distinct(
                        func.concat(
                            Finding.product_id, ",", Finding.host, ":", Finding.port
                        ),
                    ),
                    type_=ARRAY(String),
                ).label("products"),
                *CVE.__table__.columns,
            )
            .select_from(Finding)
            .join(FindingName)
            .join(CVE)
            .join_from(FindingName, Product)
            .join(Environment)
            .where(CVE.priority.in_(priorities), Environment.project_id == project_id)
            .group_by(FindingName.name, *CVE.__table__.columns)
            .order_by(CVE.priority.desc())
        )

        if filters.get("order_by"):
            direction = filters.get("order_direction")
            if direction == "desc":
                stmt = stmt.order_by(Product.name.desc())
            else:
                stmt = stmt.order_by(Product.name)
        hosts = filters.get("hosts")
        if hosts is not None:
            stmt = stmt.where(Finding.host.in_(hosts))

        return await self.pagination(stmt, page, False)

    async def adhoc_statitics(self, filters: dict, year: int | None = None):
        if year is None:
            ...
