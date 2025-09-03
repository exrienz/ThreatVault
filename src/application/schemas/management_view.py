from enum import Enum
from uuid import UUID

from pydantic import BaseModel, PositiveInt


class DirectionEnum(Enum):
    asc = "asc"
    desc = "desc"


class MVBaseSchema(BaseModel):
    project_id: UUID
    year: int | None = None
    page: PositiveInt = 1
    order_by: str | None = None
    order_direction: DirectionEnum = DirectionEnum.asc


class PriorityAPISchema(MVBaseSchema):
    product_name: str | None = None
    sensitive_hosts_view: bool = False


class SlaBreachSchema(MVBaseSchema):
    month: int | None = None
