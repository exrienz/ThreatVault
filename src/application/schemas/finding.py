from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator
from pydantic_core import PydanticCustomError

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
    hosts: list[str] | None = None
    action: str
    delay_untill: datetime | None = None
    remark: str = ""
    current_status: str | None = None

    @field_validator("delay_untill", mode="after")
    @classmethod
    def datetime_validator(cls, value: datetime | None) -> datetime | None:
        if value is not None:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if value < today:
                raise PydanticCustomError(
                    "Invalid datetime range",
                    "{value} must be greater than today date ({today}).",
                    {
                        "value": value.strftime("%d-%m-%Y"),
                        "today": today.strftime("%d-%m-%Y"),
                    },
                )
        return value


class FindingActionInternalSchema(BaseModel):
    status: FnStatusEnum
    delay_untill: datetime | None = None
    remark: str = ""
