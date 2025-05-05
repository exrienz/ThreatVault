from datetime import datetime

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
