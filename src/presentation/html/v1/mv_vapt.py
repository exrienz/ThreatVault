from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from src.application.dependencies.service_dependency import (
    EnvServiceDep,
    FindingServiceDep,
    LogServiceDep,
    ProductServiceDep,
    ProjectManagementServiceDep,
    RemarkServiceDep,
)
from src.application.schemas import PriorityAPISchema
from src.application.schemas.management_view import SlaBreachSchema
from src.presentation.dependencies import PermissionChecker

from ..utils import templates

router = APIRouter(prefix="/management-view/vapt", tags=["VAPT - Management View"])


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request, service: Annotated[ProjectManagementServiceDep, Depends()]
):
    projects = await service.get_all_by_filters({"type_": "VA"})
    min_year = await service.min_year() or datetime.now().year
    return templates.TemplateResponse(
        request,
        "pages/management_view/vapt/index.html",
        {"projects": projects, "min_year": int(min_year), "type_": "VAPT"},
    )


@router.get("/detail", response_class=HTMLResponse)
async def detail(
    request: Request,
    service: ProjectManagementServiceDep,
    view: str | None = None,
    project_id: str | None = None,
    year: int | None = None,
):
    try:
        project_uuid = UUID(project_id)
        project = await service.get_project_by_id(project_uuid)
    except ValueError:
        return templates.TemplateResponse(request, "empty.html")
    view = view if view else "overall"
    return templates.TemplateResponse(
        request,
        f"pages/management_view/vapt/component/{view}/index.html",
        {"project": project},
    )


@router.get("/overall", response_class=HTMLResponse)
async def overall(
    request: Request,
    service: ProjectManagementServiceDep,
    log_service: LogServiceDep,
    project_id: str | None = None,
    year: int | None = None,
    view: str = "severity",
):
    try:
        project = await service.get_one_by_id(UUID(project_id))
    except Exception:
        return templates.TemplateResponse(request, "empty.html")
    data = {}
    for env in project.environment:
        dct = await log_service.get_statistic_by_env_filters(env.id, year, type_=view)
        data[f"{view}_{env.name}"] = dct
    return templates.TemplateResponse(
        request,
        "pages/management_view/vapt/component/overall/index.html",
        {"project": project, "view": view, "data": data},
    )


@router.get("/sla-breach", response_class=HTMLResponse)
async def sla_breach(
    request: Request,
    service: ProjectManagementServiceDep,
    project_id: str | None = None,
    year: int | None = None,
    month: int | None = None,
):
    if month is None:
        today = datetime.now()
        month = today.month
    try:
        project = await service.get_one_by_id(UUID(project_id))
        env_ids = {}
        for env in project.environment:
            env_ids[env.name] = env.id
    except Exception:
        return templates.TemplateResponse(request, "empty.html")
    return templates.TemplateResponse(
        request,
        "pages/management_view/vapt/component/sla_breach/index.html",
        {
            "project_id": project_id,
            "year": year,
            "project": project,
            "month": month,
            "env_ids": env_ids,
        },
    )


@router.get("/sla-breach/table", response_class=HTMLResponse)
async def get_sla_breach_table(
    request: Request,
    service: FindingServiceDep,
    remark_service: RemarkServiceDep,
    env_service: EnvServiceDep,
    data: SlaBreachSchema = Depends(),
):
    if data.month is None:
        today = datetime.now()
        data.month = today.month

    res = await service.get_sla_breach_chart_data(
        data.project_id, data.model_dump(), data.page
    )

    product_ids = [p.product_id for p in res.data]
    remark_query = await remark_service.get_all_by_product_ids(
        product_ids, {"label": "sla-breach"}
    )
    env_query = await env_service.get_by_project_id(data.project_id)
    envs = {e.id: e for e in env_query}
    remarks = {r.product_id: r.remark for r in remark_query}
    return templates.TemplateResponse(
        request,
        "pages/management_view/vapt/component/sla_breach/rows.html",
        {
            "project_id": data.project_id,
            "data": res,
            "remarks": remarks,
            "year": data.year,
            "month": data.month,
            "envs": envs,
        },
    )


@router.get(
    "/remark",
    response_class=HTMLResponse,
    dependencies=[Depends(PermissionChecker(["mv-remark:create"]))],
)
async def get_sla_breach_remark_modal(
    request: Request, product_id: UUID, label: str, service: RemarkServiceDep
):
    res = await service.get_by_filters({"product_id": product_id, "label": label})
    return templates.TemplateResponse(
        request,
        "pages/management_view/vapt/component/add_remark.html",
        {"data": res, "product_id": product_id, "label": label},
    )


@router.post(
    "/remark",
    response_class=HTMLResponse,
    dependencies=[Depends(PermissionChecker(["mv-remark:create"]))],
)
async def create_sla_breach_remark_modal(
    request: Request,
    product_id: UUID,
    service: RemarkServiceDep,
    remark: Annotated[str, Form()],
    label: Annotated[str, Form()],
):
    filters = {"product_id": product_id, "label": label}
    exists = await service.get_by_filters(filters)
    data = {**filters, "remark": remark}
    if exists:
        res = await service.update(exists.id, data)
    else:
        res = await service.create(data)
    return templates.TemplateResponse(
        request,
        "pages/management_view/vapt/component/remark_response.html",
        {"data": res},
    )


@router.get("/stats-and-reason", response_class=HTMLResponse)
async def get_stats_and_reason(
    request: Request,
    service: ProjectManagementServiceDep,
    project_id: str | None = None,
    year: int | None = None,
    month: int | None = None,
):
    month = datetime.now().month if month is None else month
    try:
        project_uuid = UUID(project_id)
        project = await service.get_project_by_id(project_uuid)
    except ValueError:
        return templates.TemplateResponse(request, "empty.html")
    return templates.TemplateResponse(
        request,
        "pages/management_view/vapt/component/statsAndReason/index.html",
        {"project_id": project_id, "year": year, "project": project, "month": month},
    )


@router.get("/stats-and-reason/table", response_class=HTMLResponse)
async def get_stats_and_reason_table(
    request: Request,
    service: FindingServiceDep,
    remark_service: RemarkServiceDep,
    product_service: ProductServiceDep,
    data: SlaBreachSchema = Depends(),
):
    res = await service.get_sla_breach_chart_data(
        data.project_id, data.model_dump(), page=data.page
    )

    product_ids = [p.product_id for p in res.data]
    remark_query = await remark_service.get_all_by_product_ids(
        product_ids, {"label": "stats-and-reason"}
    )
    remarks = {r.product_id: r.remark for r in remark_query}

    product_query = await product_service.get_all_by_ids(product_ids)

    products = {p.id: p for p in product_query}

    return templates.TemplateResponse(
        request,
        "pages/management_view/vapt/component/statsAndReason/rows.html",
        {
            "project_id": data.project_id,
            "data": res,
            "remarks": remarks,
            "products": products,
            "year": data.year,
            "month": data.month,
        },
    )


@router.get("/priority", response_class=HTMLResponse)
async def priority(
    request: Request,
    service: ProjectManagementServiceDep,
    project_id: str | None = None,
    year: int | None = None,
):
    try:
        project = await service.get_one_by_id(UUID(project_id))
    except Exception:
        return templates.TemplateResponse(request, "empty.html")
    return templates.TemplateResponse(
        request,
        "pages/management_view/vapt/component/priority/index.html",
        {"project_id": project_id, "year": year, "project": project},
    )


@router.get("/priority/table", response_class=HTMLResponse)
async def priority_data_table(
    request: Request,
    service: FindingServiceDep,
    product_service: ProductServiceDep,
    req_data: PriorityAPISchema = Depends(),
):
    data = await service.get_by_priority_threshold(req_data, ["1+", "1"])
    products_set = set()
    product_map = {}

    for d in data.data:
        for product in d.products:
            prod_str = product.split(",")
            products_set.add(prod_str[0])
            product_map[prod_str[-1]] = prod_str[0]

    products = await product_service.get_all_by_ids(list(products_set))
    products_ids = {str(product.id): product for product in products}

    for k, v in product_map.items():
        product_map[k] = products_ids.get(v)

    return templates.TemplateResponse(
        request,
        "pages/management_view/vapt/component/priority/rows.html",
        {
            "project_id": req_data.project_id,
            "year": req_data.year,
            "data": data,
            "product_map": product_map,
        },
    )
