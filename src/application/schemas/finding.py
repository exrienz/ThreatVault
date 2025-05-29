from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.domain.constant import SeverityEnum


class ManualFindingUploadSchema(BaseModel):
    finding_name: str
    host: str
    port: str
    severity: SeverityEnum
    vpr_score: str
    evidence: str
    remediation: str
    finding_date: datetime


class FindingFiltersSchema(BaseModel):
    status: list[str] | None = None
    severity: list[str] | None = None
    plugin_id: list[str] | None = None
    host: list[str] | None = None


class ITSRemark(BaseModel):
    pic_list: list[UUID] | None = None
    target_date: datetime
    reason: str
    remark: str
    product_id: UUID
