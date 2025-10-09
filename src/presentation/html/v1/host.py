from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import PositiveInt

from src.application.dependencies import (
    FindingServiceDep,
)
from src.presentation.dependencies import PermissionChecker

from ..utils import templates

router = APIRouter(prefix="/host", tags=["host"])


@router.get("", response_class=HTMLResponse)
async def get_host_finding_by_product_id(
    request: Request,
    service: FindingServiceDep,
    host: str,
):
    risk_pagination = await service.get_group_by_assets(filters={"host": (host,)})
    risk = risk_pagination.get("findings")
    risk_data = risk.data[0] if risk else None
    total_severity = 1
    if risk_data:
        total_severity = sum(risk_data[1:-1])

    finding = await service.get_first_by_filters({"host": host})
    return templates.TemplateResponse(
        request,
        "pages/host/index.html",
        {
            "host": host,
            "logs": risk_data,
            "totalSeverity": total_severity,
            "finding": finding,
        },
    )


@router.get("/findings", response_class=HTMLResponse)
async def get_findings(
    request: Request,
    service: FindingServiceDep,
    host: str,
    page: PositiveInt = 1,
):
    data = await service.get_group_by_asset_details(host, {}, page)
    return templates.TemplateResponse(
        request,
        "pages/host/component/table.html",
        {"findings": data},
    )


@router.delete(
    "/{product_id}/{host}", dependencies=[Depends(PermissionChecker(["host:delete"]))]
)
async def delete_host(
    request: Request,
    service: FindingServiceDep,
    product_id: UUID,
    host: str,
):
    await service.delete_by_filter(product_id, {"host": (host,)})
