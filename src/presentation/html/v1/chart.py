from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse

from src.application.dependencies.service_dependency import (
    EnvServiceDep,
    FindingServiceDep,
    LogServiceDep,
    ProductServiceDep,
    ProjectManagementServiceDep,
)
from src.application.schemas.chart import (
    YearlyProductStatisticsSchema,
    YearlyStatisticFilterSchema,
    YearlyStatsRequestSchema,
)

from ..utils import templates

router = APIRouter(prefix="/chart", tags=["Chart"])


@router.get("/project/{project_id}", response_class=HTMLResponse)
async def get_project_yearly_stats(
    request: Request,
    service: ProjectManagementServiceDep,
    log_service: LogServiceDep,
    env_service: EnvServiceDep,
    project_id: UUID,
    req_data: Annotated[YearlyStatsRequestSchema, Query()],
):
    project = await service.get_project_by_id(project_id)
    if project is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID({project_id}) does not exists",
        )
    env = await env_service.get_by_filter(project.id, req_data.env)
    if env is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"{req_data.env} environment for {project.name} does not exists",
        )
    filters = YearlyStatisticFilterSchema(
        # project_id=project_id,
        year=req_data.year,
        view_type=req_data.view_type,
        env_id=env.id,
    )
    chart, *_, labels = await log_service.get_yearly_statistics(filters)
    return templates.TemplateResponse(
        request,
        f"shared/charts/{req_data.view_type}_year.html",
        {
            "chart": chart,
            "env": req_data.env,
            "project_type": project.type_,
            "labels": labels,
        },
    )


@router.get("/product", response_class=HTMLResponse)
async def get_product_yearly_stats(
    request: Request,
    log_service: LogServiceDep,
    req_data: Annotated[YearlyProductStatisticsSchema, Query()],
):
    chart, _, labels = await log_service.get_product_yearly_statistics(req_data)
    return templates.TemplateResponse(
        request,
        f"shared/charts/{req_data.view_type}_year.html",
        {
            "chart": chart,
            "labels": labels,
            "env": "product",
            "update": req_data.update,
        },
    )


@router.get("/product/risk", response_class=HTMLResponse)
async def get_product_risk_latest(
    request: Request,
    log_service: LogServiceDep,
    product_id: UUID,
    update: bool = False,
):
    data = await log_service.get_risks(product_id)
    chart_data = []
    if data:
        chart_data = [data.tCritical, data.tHigh, data.tMedium, data.tLow]
    return templates.TemplateResponse(
        request,
        "shared/charts/product_risk.html",
        {"data": chart_data, "update": update},
    )


@router.get("/host/risk", response_class=HTMLResponse)
async def get_host_risk_latest(
    request: Request,
    service: FindingServiceDep,
    host: str,
    update: bool = False,
):
    risk_pagination = await service.get_group_by_assets(filters={"host": (host,)})
    risk = risk_pagination.get("findings")
    risk_data = risk.data[0] if risk else None
    if risk_data:
        risk_data = [risk_data[4], risk_data[3], risk_data[2], risk_data[1]]
    return templates.TemplateResponse(
        request,
        "shared/charts/product_risk.html",
        {"data": risk_data, "update": update},
    )


@router.get("/env")
async def get_aging_chart_env(
    request: Request,
    service: LogServiceDep,
    envService: EnvServiceDep,
    productService: ProductServiceDep,
    req_data: Annotated[YearlyStatisticFilterSchema, Query()],
):
    if req_data.env_id is None:
        raise
    env = await envService.get_by_id(req_data.env_id)
    if env is None:
        raise
    project_type = env.project.type_
    date_start = await service.get_first_date_track_by_env(req_data.env_id)

    data = await service.get_products_by_env(req_data)
    products = await productService.get_by_env_id(req_data.env_id)

    return templates.TemplateResponse(
        request,
        "shared/charts/compare_card.html",
        {
            **data,
            "env": env,
            "products": products,
            "view": req_data.view_type,
            "project_type": project_type,
            "start_dt_opts": date_start,
        },
    )


@router.get("/sla-breach/products")
async def sla_breach_by_env(
    request: Request,
    service: LogServiceDep,
    env_id: UUID,
    severity: str | None = None,
    year: int | None = None,
):
    year = year if year else datetime.now().year
    chart_data = await service.get_logs_yearly_env(env_id, year, severity)
    return templates.TemplateResponse(
        request,
        "shared/charts/sla_breach_products.html",
        {
            "data": chart_data,
            "year": year,
        },
    )


@router.get("/sla-breach/env")
async def get_sla_breach(
    request: Request,
    finding_service: FindingServiceDep,
    project_id: UUID,
    env: str | None = "production",
    date_str: datetime | None = None,
    year: int | None = None,
    month: int | None = None,
):
    if date_str:
        year, month = date_str.year, date_str.month
    today = datetime.now()
    year = year if year else today.year
    month = month if month else today.month

    data = await finding_service.get_sla_breach_summary(
        project_id, {"year": year, "month": month, "env_type": env}
    )
    chart_ = data._asdict()
    if chart_.get("CRITICAL") is None:
        chart_ = {}
    labels = []
    chart_data = []

    for k, v in chart_.items():
        labels.append(k)
        chart_data.append(v)
    return templates.TemplateResponse(
        request,
        "shared/charts/sla_breach_env.html",
        {
            "data": chart_data,
            "labels": labels,
            "year": year,
            "month": month,
            "env": env,
        },
    )
