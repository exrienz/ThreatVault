from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime

from src.domain.constant import FnStatusEnum, SeverityEnum

from .base import Base


class Finding(Base):
    __tablename__ = "finding"

    host: Mapped[str]
    port: Mapped[str]
    status: Mapped[FnStatusEnum]
    severity: Mapped[SeverityEnum]
    reopen: Mapped[bool] = mapped_column(server_default="f")
    vpr_score: Mapped[Optional[str]]
    evidence: Mapped[str]
    remediation: Mapped[str]
    remark: Mapped[Optional[str]]
    internal_remark: Mapped[Optional[str]]
    finding_date: Mapped[datetime] = mapped_column(DateTime(True))  # First Scan Date
    last_update: Mapped[datetime] = mapped_column(DateTime(True))  # Latest Scan Date
    delay_untill: Mapped[Optional[datetime]] = mapped_column(DateTime(True))
    closing_effort: Mapped[Optional[int]]
    label: Mapped[Optional[str]]

    # product_id: Mapped[UUID] = mapped_column(ForeignKey("product.id"))
    plugin_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("plugin.id"))
    finding_name_id: Mapped[UUID] = mapped_column(ForeignKey("finding_name.id"))
    finding_name = relationship("FindingName")

    __table_args__ = (
        Index(
            "uix_unique_finding_except_closed",
            "finding_name_id",
            "host",
            "port",
            "plugin_id",
            unique=True,
            postgresql_where=(Column("status") != FnStatusEnum.CLOSED.value),
        ),
    )


class FindingRevertPoint(Base):
    __tablename__ = "finding_revert_point"

    status: Mapped[FnStatusEnum]
    severity: Mapped[SeverityEnum]
    reopen: Mapped[bool] = mapped_column(server_default="f")
    vpr_score: Mapped[Optional[str]]
    evidence: Mapped[str]
    remediation: Mapped[str]
    # remark: Mapped[Optional[str]]
    internal_remark: Mapped[Optional[str]]
    finding_date: Mapped[datetime] = mapped_column(DateTime(True))
    last_update: Mapped[datetime] = mapped_column(DateTime(True))
    label: Mapped[Optional[str]]

    finding_name_id: Mapped[UUID] = mapped_column(ForeignKey("finding_name.id"))


class Plugin(Base):
    __tablename__ = "plugin"

    name: Mapped[str]
    description: Mapped[Optional[str]]
    is_active: Mapped[bool] = mapped_column(server_default="f")
    type: Mapped[str]  # builtin or custom
    env: Mapped[Optional[str]]  # VA or HA
    config: Mapped[Optional[str]]  # JSON?
    verified: Mapped[bool] = mapped_column(server_default="f")
    # verification_error: Mapped[Optional[str]]
    # file_path: Mapped[Optional[str]]


class FindingName(Base):
    __tablename__ = "finding_name"
    name: Mapped[str]

    description: Mapped[Optional[str]]

    product_id: Mapped[UUID] = mapped_column(ForeignKey("product.id"))
    product = relationship("Product")
    findings = relationship("Finding", back_populates="finding_name")

    cves = relationship("CVE", back_populates="finding_name")

    __table_args__ = (
        Index(
            "idx_finding_name_product",
            "name",
            "product_id",
            unique=True,
        ),
    )


class CVE(Base):
    __tablename__ = "cve"

    name: Mapped[str]
    priority: Mapped[str]  # TODO: enum?
    epss: Mapped[Optional[str]]
    kevList: Mapped[bool] = mapped_column(server_default="f")
    severity: Mapped[SeverityEnum] = mapped_column(default=SeverityEnum.LOW)
    vector: Mapped[Optional[str]]

    finding_name_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("finding_name.id")
    )
    finding_name = relationship("FindingName", back_populates="cves")

    __table_args__ = (
        UniqueConstraint(
            "name",
            name="uix_cve",
        ),
    )


class Comment(Base):
    __tablename__ = "comment"

    comment: Mapped[str]
    findingName_id: Mapped[UUID] = mapped_column(ForeignKey("finding_name.id"))
    commentor_id: Mapped[UUID] = mapped_column(ForeignKey("auth_user.id"))
    commentor = relationship("User")


class Log(Base):
    __tablename__ = "log"

    tCritical: Mapped[int] = mapped_column(default=0)
    tHigh: Mapped[int] = mapped_column(default=0)
    tMedium: Mapped[int] = mapped_column(default=0)
    tLow: Mapped[int] = mapped_column(default=0)
    tPass: Mapped[int] = mapped_column(default=0)
    tFail: Mapped[int] = mapped_column(default=0)
    tNew: Mapped[int] = mapped_column(default=0)
    tOpen: Mapped[int] = mapped_column(default=0)
    tClosed: Mapped[int] = mapped_column(default=0)
    tExamption: Mapped[int] = mapped_column(default=0)
    tOthers: Mapped[int] = mapped_column(default=0)
    bCrit: Mapped[int] = mapped_column(default=0)
    bHigh: Mapped[int] = mapped_column(default=0)
    bMedium: Mapped[int] = mapped_column(default=0)
    bLow: Mapped[int] = mapped_column(default=0)

    product_id: Mapped[UUID] = mapped_column(ForeignKey("product.id"))
    log_date: Mapped[datetime] = mapped_column(DateTime(True))
    uploader_id: Mapped[UUID] = mapped_column(ForeignKey("auth_user.id"))
    uploader = relationship("User")

    product = relationship("Product")
