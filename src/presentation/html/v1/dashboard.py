from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.application.dependencies.service_dependency import (
    EnvServiceDep,
    LogServiceDep,
    ProjectManagementServiceDep,
)
from src.config import sidebar_items

from ..utils import templates

router = APIRouter(tags=["Dashboard"])


@router.get("/")
async def get_dashboard(request: Request, service: ProjectManagementServiceDep):
    projects = await service.get_all_with_logs()
    return templates.TemplateResponse(
        request,
        "pages/dashboard/index.html",
        {"projects": projects, "sidebarItems": sidebar_items},
    )


@router.get("/project/{project_id}", response_class=HTMLResponse)
async def get_project_dashboard(
    request: Request,
    service: ProjectManagementServiceDep,
    logService: LogServiceDep,
    project_id: UUID,
):
    project = await service.get_project_extended(project_id)
    chart = {}
    prod_env = None
    nonprod_env = None
    for env in project[0].environment:
        if env.name == "production":
            prod_env = env
            chart["prod"], *_ = await logService.get_statistic_by_env(env.id)
        else:
            nonprod_env = env
            chart["nonprod"], *_ = await logService.get_statistic_by_env(env.id)

    return templates.TemplateResponse(
        request,
        "pages/dashboard/project.html",
        {
            "project": project[0],
            "sidebarItems": sidebar_items,
            "chart": chart,
            "prod_env": prod_env,
            "nonprod_env": nonprod_env,
            "curr_date": datetime.now(),
        },
    )


# TODO: Chart in one route
@router.get("/chart/env/{env_id}")
async def get_aging_chart_env(
    request: Request,
    service: LogServiceDep,
    envService: EnvServiceDep,
    env_id: UUID,
    date_str: datetime | None = None,
    year: int | None = None,
    month: int | None = None,
):
    env = await envService.get_by_id(env_id)
    if date_str:
        year, month = date_str.year, date_str.month
    data, year, month = await service.get_products_by_env(env_id, year, month)
    data_dct = {row.product_id: row for row in data}
    total = [0, 0, 0, 0]
    date_options = await service.get_available_date_by_env(env_id)
    for d in data:
        total[0] += d.tCritical
        total[1] += d.tHigh
        total[2] += d.tMedium
        total[3] += d.tLow

    return templates.TemplateResponse(
        request,
        "pages/dashboard/component/compareCard.html",
        {
            "data": data_dct,
            "total": total,
            "env": env,
            "year": year,
            "month": month,
            "date_options": date_options,
        },
    )
