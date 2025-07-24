from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse

from src.application.dependencies.service_dependency import (
    EnvServiceDep,
    FindingServiceDep,
    LogServiceDep,
    ProductServiceDep,
    ProjectManagementServiceDep,
)

from ..utils import templates

router = APIRouter(prefix="/chart", tags=["Chart"])


@router.get("/project/{project_id}", response_class=HTMLResponse)
async def get_project_dashboard(
    request: Request,
    service: ProjectManagementServiceDep,
    logService: LogServiceDep,
    project_id: UUID,
    env: str = "prod",
    year: int | None = None,
    view: str = "severity",
):
    project = await service.get_project_by_id(project_id)
    if project is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID({project_id}) cannot be found!",
        )

    env_id = None
    for pr_env in project.environment:
        if pr_env.name.startswith(env):
            env_id = pr_env.id
    chart = None
    if env_id:
        chart, *_ = await logService.get_statistic_by_env_filters(
            env_id, year, type_=view
        )
    return templates.TemplateResponse(
        request,
        f"shared/charts/{view}_year.html",
        {"chart": chart, "env": env},
    )


@router.get("/env")
async def get_aging_chart_env(
    request: Request,
    service: LogServiceDep,
    envService: EnvServiceDep,
    productService: ProductServiceDep,
    env_id: UUID,
    date_str: datetime | None = None,
    year: int | None = None,
    month: int | None = None,
    view: str = "severity,",
):
    env = await envService.get_by_id(env_id)
    if date_str:
        year, month = date_str.year, date_str.month
    data, year, month = await service.get_products_by_env(env_id, year, month)
    data_dct = {row.product_id: row for row in data}
    date_options = await service.get_available_date_by_env(env_id)

    total = [0, 0, 0, 0]
    for d in data:
        if view == "severity":
            total[0] += d.tCritical
            total[1] += d.tHigh
            total[2] += d.tMedium
            total[3] += d.tLow
        else:
            total[0] += d.tOpen
            total[1] += d.tNew
            total[2] += d.tClosed + d.tOthers
            total[3] += d.tExemption

    products = await productService.get_by_env_id(env_id)

    return templates.TemplateResponse(
        request,
        "shared/charts/compare_card.html",
        {
            "data": data_dct,
            "total": total,
            "env": env,
            "products": products,
            "year": year,
            "month": month,
            "date_options": date_options,
            "view": view,
        },
    )


@router.get("/sla-breach", response_class=HTMLResponse)
async def get_project_sla_breached(
    request: Request,
    service: ProjectManagementServiceDep,
    finding_service: FindingServiceDep,
    project_id: UUID,
    env: str = "prod",
    month: int | None = None,
    year: int | None = None,
):
    today = datetime.now()
    month = month if month else today.month
    year = year if year else today.year

    project = await service.get_project_by_id(project_id)
    if project is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID({project_id}) cannot be found!",
        )

    data = await finding_service.get_sla_breach_status(project_id)
    chart_data = []
    for d in data:
        chart_data.append(
            {"name": d.product_name, "data": [d.CRITICAL, d.MEDIUM, d.HIGH, d.LOW]}
        )
    return templates.TemplateResponse(
        request,
        "shared/charts/sla_breach_card_v2.html",
        {
            "data": chart_data,
        },
    )


@router.get("/sla-breach/products")
async def get_aging_chart_env_v2(
    request: Request,
    finding_service: FindingServiceDep,
    project_service: ProjectManagementServiceDep,
    log_service: LogServiceDep,
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
    project = await project_service.get_project_by_id(project_id)

    data = await finding_service.get_sla_breach_status(project_id, env)
    chart_ = {"LOW": [], "MEDIUM": [], "HIGH": [], "CRITICAL": []}
    categories = []
    for d in data:
        categories.append(d.product_name)
        chart_["LOW"].append(d.LOW)
        chart_["MEDIUM"].append(d.MEDIUM)
        chart_["HIGH"].append(d.HIGH)
        chart_["CRITICAL"].append(d.CRITICAL)

    chart_data = []
    for k, v in chart_.items():
        chart_data.append({"name": k, "data": v})
    return templates.TemplateResponse(
        request,
        "shared/charts/sla_breach_products.html",
        {
            "data": chart_data,
            "categories": categories,
            "year": year,
            "month": month,
            "project": project,
            "env": env,
        },
    )


@router.get("/sla-breach/product")
async def get_sla_breach_yearly(
    request: Request,
    log_service: LogServiceDep,
    product_service: ProductServiceDep,
    product_name: str,
    env_id: UUID,
    year: int | None = None,
):
    product = await product_service.get_one_by_filter(
        {"name": product_name, "environment_id": env_id}
    )
    if product is None:
        data = []
    else:
        data = await log_service.get_logs_yearly(product.id, year)

    data_dict = {
        "Low": [0] * 12,
        "Medium": [0] * 12,
        "High": [0] * 12,
        "Critical": [0] * 12,
    }
    for d in data:
        for k in data_dict.keys():
            data_dict[k][int(d.month) - 1] = getattr(d, f"b{k}")

    chart_data = [{"name": k, "data": v} for k, v in data_dict.items()]
    return templates.TemplateResponse(
        request,
        "shared/charts/sla_breach_yearly.html",
        {
            "data": chart_data,
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
        chart_ = {"CRITICAL": 1, "HIGH": 1, "MEDIUM": 1, "LOW": 1}
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
