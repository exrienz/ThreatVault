from datetime import datetime
from uuid import UUID

from fastapi import APIRouter

from src.application.dependencies.service_dependency import (
    LogServiceDep,
)

router = APIRouter(prefix="/chart", tags=["Chart_API"])


@router.get("/sla-breach/products")
async def get_sla_breach_yearly(
    service: LogServiceDep,
    env_id: UUID,
    severity: str | None = None,
    year: int | None = None,
):
    year = year if year else datetime.now().year
    return await service.get_logs_yearly_env(env_id, year, severity)
