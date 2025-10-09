from collections.abc import Sequence
from datetime import datetime
from typing import Annotated
from uuid import UUID

import polars as pl
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

from src.domain.constant import FnStatusEnum, HAStatusEnum, SeverityEnum, VAStatusEnum
from src.domain.entity import Finding, FindingName
from src.domain.entity.finding import CVE
from src.domain.entity.project_management import Environment, Product, Project
from src.domain.entity.setting import GlobalConfig
from src.infrastructure.database import get_session
from src.persistence.base import BaseRepository, Pagination
from src.presentation.dependencies import get_allowed_product_ids


class FindingRepository(BaseRepository[Finding]):
    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(get_session)],
        product_ids: Annotated[list[UUID] | None, Depends(get_allowed_product_ids)],
    ):
        super().__init__(Finding, session, product_ids=product_ids)

    def _options(self, stmt: Select):
        return stmt.options(
            selectinload(Finding.finding_name),
            selectinload(Finding.product).selectinload(Product.environment),
        )

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
        stmt = self._product_allowed_ids(stmt)
        query = await self.session.execute(stmt)
        return query.scalar()

    async def get_all_by_project_id(
        self, project_id: UUID, active_only: bool = False
    ) -> Sequence[Finding]:
        stmt = (select(Finding).join(Product).join(Environment)).where(
            Environment.project_id == project_id
        )

        stmt = stmt.options(
            selectinload(Finding.finding_name),
            selectinload(Finding.product).selectinload(Product.environment),
        )

        if active_only:
            exception_list = [
                VAStatusEnum.CLOSED.value,
                VAStatusEnum.EXEMPTION.value,
                VAStatusEnum.OTHERS.value,
                HAStatusEnum.PASSED.value,
            ]
            stmt = stmt.where(Finding.status.notin_(exception_list))
        stmt = self._product_allowed_ids(stmt)
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
        stmt = self._product_allowed_ids(stmt)
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

        stmt = self._product_allowed_ids(stmt)
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
        stmt = self._product_allowed_ids(stmt)
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

        stmt = self._product_allowed_ids(stmt)
        return await self.pagination(stmt, page)

    async def get_group_by_evidence(self, filters: dict):
        stmt = select(
            Finding.evidence,
            func.max(Finding.status),
            func.max(Finding.severity),
            func.array_agg(
                func.distinct(
                    func.concat(Finding.host, ":", Finding.port),
                ),
                type_=ARRAY(String),
            ).label("hosts"),
        ).group_by(Finding.evidence)
        stmt = self._filters(stmt, filters)
        stmt = self._permission_filter(stmt)
        query = await self.session.execute(stmt)
        return query.all()

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
                Finding.status.not_in(
                    [FnStatusEnum.CLOSED.value, FnStatusEnum.EXEMPTION.value]
                ),
                Finding.severity == severity.value,
                func.extract("day", Finding.finding_date - today) < sub,
            )
        ).group_by(FindingName.id, FindingName.name, Finding.severity)

        stmt = self._product_allowed_ids(stmt)
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
        stmt = self._product_allowed_ids(stmt)
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
                Finding.status != FnStatusEnum.CLOSED.value,
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

        stmt = self._product_allowed_ids(stmt)

        return await self.pagination(stmt, page, False)

    async def adhoc_statitics(self, filters: dict, year: int | None = None):
        if year is None:
            ...

    def _product_allowed_ids(self, stmt: Select) -> Select:
        if self.allowed_product_ids is None:
            return stmt
        return stmt.where(Finding.product_id.in_(self.allowed_product_ids))

    async def export_active_findings(self, project_id: UUID) -> pl.DataFrame:
        exception_list = [
            VAStatusEnum.CLOSED.value,
            VAStatusEnum.EXEMPTION.value,
            VAStatusEnum.OTHERS.value,
            HAStatusEnum.PASSED.value,
        ]

        stmt = (
            select(
                cast(Finding.id, String).label("id"),
                Product.name.label("product"),
                Environment.name.label("environment"),
                Finding.finding_date,
                Finding.last_update,
                Finding.severity,
                Finding.host,
                Finding.port,
                Finding.evidence,
                Finding.remediation,
                FindingName.description.label("description"),
            )
            .select_from(Finding)
            .join(Product)
            .join(Environment, Product.environment_id == Environment.id)
            .join(FindingName, Finding.finding_name_id == FindingName.id)
        ).where(
            Finding.status.notin_(exception_list),
            Environment.project_id == project_id,
        )

        stmt = self._product_allowed_ids(stmt)

        query = await self.session.execute(stmt)
        rows = query.all()
        df = pl.DataFrame(rows, schema=[str(col.key) for col in stmt.selected_columns])

        df = df.with_columns(
            pl.col("severity").map_elements(
                lambda x: x.value if x else "", return_dtype=pl.String
            )
        )
        cve_stmt = (
            select(cast(Finding.id, String), CVE.name.label("cve"))
            .select_from(Finding)
            .join(FindingName)
            .join(CVE)
            .join(Product, Finding.product_id == Product.id)
            .join(Environment)
            .where(Environment.project_id == project_id)
        )
        cve_stmt = self._product_allowed_ids(cve_stmt)
        cve_query = await self.session.execute(cve_stmt)
        cve_rows = cve_query.all()
        cve_df = pl.DataFrame(cve_rows, schema=["id", "cve"])
        cve_grouped = cve_df.group_by("id").agg(
            pl.col("cve").map_elements(
                lambda lst: ",".join(map(str, lst)), return_dtype=pl.String
            )
        )

        df = df.join(cve_grouped, on="id", how="left").drop("id")
        df = df.with_columns(
            pl.col(pl.String)
            .str.replace_all(r"\s*<br\s*/?>\s*", " ")
            .str.replace_all(r"\s+", " ")
            .str.strip_chars()
        )
        return df

    async def report_finding_generation(
        self,
        product_id: UUID | None = None,
    ) -> Sequence:
        exception_list = [
            VAStatusEnum.CLOSED.value,
            VAStatusEnum.EXEMPTION.value,
            VAStatusEnum.OTHERS.value,
            HAStatusEnum.PASSED.value,
        ]
        stmt = (
            (
                select(
                    FindingName.id,
                    func.max(FindingName.name).label("name"),
                    func.max(FindingName.description).label("description"),
                    Finding.severity,
                    func.max(Finding.remediation).label("remediation"),
                ).join(Finding)
            )
            .where(
                Finding.status.not_in(exception_list), Finding.product_id == product_id
            )
            .group_by(FindingName.id, Finding.severity)
            .order_by(Finding.severity)
        )
        stmt = self._product_allowed_ids(stmt)
        query = await self.session.execute(stmt)
        findings = query.all()

        evidence_stmt = (
            select(
                Finding.finding_name_id,
                Finding.evidence,
                func.array_agg(func.distinct(Finding.host), type_=ARRAY(String)).label(
                    "hosts"
                ),
            )
            .where(Finding.product_id == product_id)
            .group_by(Finding.finding_name_id, Finding.evidence)
        )
        evidence_stmt = self._product_allowed_ids(evidence_stmt)
        query = await self.session.execute(evidence_stmt)
        evidences = query.all()
        evidences_dict: dict[UUID, list] = {}
        for ev in evidences:
            data = evidences_dict.get(ev.finding_name_id)
            if data:
                data.append(ev)
            else:
                evidences_dict[ev.finding_name_id] = [ev]

        return findings, evidences_dict
