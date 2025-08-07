from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class BaseSchema(BaseModel):
    year: int | None = None
    view_type: str = "severity"


class YearlyStatsRequestSchema(BaseSchema):
    env: str = "production"


class YearlyStatisticFilterSchema(BaseSchema):
    env_id: UUID | None = None
    project_id: UUID | None = None
    month: int | None = None
    date_str: datetime | None = None


class YearlyProductStatisticsSchema(BaseSchema):
    product_id: UUID
