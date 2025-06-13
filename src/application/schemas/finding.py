from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from src.domain.constant import FnStatusEnum, SeverityEnum


class FindingUploadSchema(BaseModel):
    scan_date: datetime
    plugin: UUID
    process_new_finding: bool = False
    sync_update: bool = False


class ManualFindingUploadSchema(BaseModel):
    finding_name: str
    host: str
    port: int
    severity: SeverityEnum
    vpr_score: int
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


class FindingActionRequestSchema(BaseModel):
    finding_name_id: UUID
    choices: list[str]
    action: str
    delayUntill: Optional[datetime]
    remarks: str = ""


class FindingActionInternalSchema(BaseModel):
    status: FnStatusEnum
    delayUntill: Optional[datetime]
    remarks: str = ""
    host_list: list[str]
