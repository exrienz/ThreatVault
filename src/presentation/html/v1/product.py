import json
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import PositiveInt
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dependencies import (
    FindingServiceDep,
    LogServiceDep,
    PluginServiceDep,
    ProductServiceDep,
    UserServiceDep,
)
from src.application.schemas.finding import (
    FindingFiltersSchema,
    ManualFindingUploadSchema,
)
from src.application.services import FileUploadService
from src.config import sidebar_items
from src.domain.constant import FnStatusEnum
from src.infrastructure.database.session import get_session

from ..utils import templates

router = APIRouter(prefix="/product", tags=["product"])


@router.get("/{product_id}", response_class=HTMLResponse)
async def get_product(
    request: Request,
    service: ProductServiceDep,
    log_service: LogServiceDep,
    plugin_service: PluginServiceDep,
    product_id: UUID,
):
    product = await service.get_by_id(product_id)
    logs = await log_service.get_by_product_id(product_id)
    plugins = await plugin_service.get_all_activated()
    tSeverity = 1
    if logs:
        tSeverity = logs.tCritical + logs.tHigh + logs.tMedium + logs.tLow

    return templates.TemplateResponse(
        request,
        "pages/product/index.html",
        {
            "sidebarItems": sidebar_items,
            "product": product,
            "logs": logs,
            "totalSeverity": tSeverity,
            "plugins": plugins,
        },
    )


@router.get("/{product_id}/findings", response_class=HTMLResponse)
async def get_findings(
    request: Request,
    finding_service: FindingServiceDep,
    product_id: UUID,
    page: PositiveInt = 1,
):
    filters = request.session.get("finding-selected")
    findings, sla_mapping = await finding_service.get_group_by_severity_status(
        product_id, page, filters
    )
    return templates.TemplateResponse(
        request,
        "pages/product/response/findings.html",
        {"findings": findings, "product_id": product_id, "sla": sla_mapping},
    )


@router.post("/finding/action")
async def finding_action(
    request: Request,
    finding_name_id: Annotated[UUID, Form()],
    choices: Annotated[list[str], Form()],
    action: Annotated[str, Form()],
    delayUntill: Annotated[datetime, Form()],
    remarks: Annotated[str, Form()],
    finding_service: FindingServiceDep,
):
    try:
        status = FnStatusEnum(action.upper())
    except Exception:
        status = FnStatusEnum.OTHER
        remarks = remarks + f"\n System: {action}"

    data = {
        "status": status,
        "delay_untill": delayUntill,
        "remark": remarks,
    }
    await finding_service.update(finding_name_id, choices, data)
    return templates.TemplateResponse(
        request,
        "empty.html",
        headers={"HX-Trigger": "reload-findings"},
    )


@router.post("/{product_id}/upload", response_class=HTMLResponse)
async def upload_file(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    log_service: LogServiceDep,
    user_service: UserServiceDep,
    product_id: UUID,
    scan_date: Annotated[datetime, Form()],
    plugin: Annotated[UUID, Form()],
    formFile: Annotated[UploadFile, File()],
    process_new_finding: Annotated[bool, Form()] = False,
    sync_update: Annotated[bool, Form()] = False,
):
    """
    TODO:
        - All the error handling
        - Sync Update
    """
    fileupload = FileUploadService(
        session,
        formFile,
        plugin,
        scan_date,
        product_id,
        process_new_finding,
        sync_update,
    )
    await fileupload.upload()
    tSeverity = 1
    logs = await log_service.calculate(product_id, fileupload.scan_date)
    user = None
    if logs:
        tSeverity = logs.tCritical + logs.tHigh + logs.tMedium + logs.tLow
        user = await user_service.get_by_id(logs.uploader_id)
    return templates.TemplateResponse(
        request,
        "pages/product/response/fileupload.html",
        headers={"HX-Trigger": "reload-findings"},
        context={"logs": logs, "totalSeverity": tSeverity, "user": user},
    )


@router.post("/{product_id}/upload/manual")
async def manual_upload(
    request: Request,
    service: FindingServiceDep,
    product_id: UUID,
    data: Annotated[ManualFindingUploadSchema, Form()],
):
    await service.manual_upload(
        {"name": data.finding_name, "product_id": product_id},
        data.model_dump(exclude={"finding_name"}),
    )


@router.get("/{product_id}/aging-finding-chart", response_class=HTMLResponse)
async def aging_finding_chart(
    request: Request, service: LogServiceDep, product_id: UUID
):
    year = datetime.now().year
    chart_info = await service.statistic(product_id, year)

    dct = {
        "Critical": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "High": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "Medium": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "Low": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    }
    for c in chart_info:
        mnt = int(c.month) - 1
        dct["Critical"][mnt] = c.tCritical
        dct["High"][mnt] = c.tHigh
        dct["Medium"][mnt] = c.tMedium
        dct["Low"][mnt] = c.tLow

    return templates.TemplateResponse(
        request,
        "pages/product/response/agingChart.html",
        context={"data": dct},
    )


@router.get("/{product_id}/user-permissions")
async def get_permission(request: Request, product_id: UUID):
    return templates.TemplateResponse(
        request,
        "pages/product/response/permissionModal.html",
        {"product_id": product_id},
    )


@router.get("/{product_id}/user-list")
async def get_with_permission_list(
    request: Request,
    product_id: UUID,
    service: ProductServiceDep,
    allowed: bool = True,
):
    users = await service.get_products_user_accessible_list(
        product_id, allowed, exclude_roles=["Owner"]
    )
    return templates.TemplateResponse(
        request,
        "pages/product/component/userList.html",
        {"product_id": product_id, "users": users, "allowed": allowed},
    )


@router.post("/{product_id}/user-permission")
async def toggle_user_permission(
    request: Request,
    service: ProductServiceDep,
    product_id: UUID,
    user_id: Annotated[UUID, Form()],
    granted: Annotated[bool, Form()] = True,
):
    await service.manage_product_access(product_id, user_id, granted)


@router.post("/{product_id}/generate-api-key")
async def generate_api_key(
    request: Request, service: ProductServiceDep, product_id: UUID
):
    product = await service.generate_api_key(product_id)
    return templates.TemplateResponse(
        request, "pages/product/response/tokenGeneration.html", {"product": product}
    )


@router.get("/{product_id}/escalation")
async def get_escalation_list(request: Request, service: UserServiceDep):
    data = await service.get_all()
    return templates.TemplateResponse(
        request, "pages/product/response/escalation.html", {"users": data}
    )


@router.post("/{product_id}/escalation")
async def escalation_list(
    request: Request,
    service: UserServiceDep,
    user_ids: Annotated[list[UUID], Form()],
    weekly: Annotated[bool, Form()],
    monthly: Annotated[bool, Form()],
):
    data = await service.get_all()
    return templates.TemplateResponse(
        request, "pages/product/response/escalation.html", {"users": data}
    )


@router.get("/{product_id}/revert")
async def revert_modal(
    request: Request,
    service: LogServiceDep,
    finding_service: FindingServiceDep,
    product_id: UUID,
):
    current = await service.get_by_product_id(product_id)
    prev = await service.get_prev_by_product_id(product_id)
    keys = ["tNew", "tOpen", "tClosed", "tExamption", "tOthers"]
    can_revert = await finding_service.can_revert(product_id)
    return templates.TemplateResponse(
        request,
        "pages/product/response/revertModal.html",
        {
            "prev": prev,
            "keys": keys,
            "current": current,
            "product_id": product_id,
            "can_revert": can_revert,
        },
    )


@router.post("/{product_id}/revert")
async def revert(
    request: Request,
    service: FindingServiceDep,
    log_service: LogServiceDep,
    user_service: UserServiceDep,
    product_id: UUID,
):
    await service.revert(product_id)

    logs = await log_service.get_by_product_id(product_id)
    tSeverity = 1
    user = None
    if logs:
        tSeverity = logs.tCritical + logs.tHigh + logs.tMedium + logs.tLow
        user = await user_service.get_by_id(logs.uploader_id)

    return templates.TemplateResponse(
        request,
        "pages/product/response/fileupload.html",
        headers={"HX-Trigger": "reload-findings"},
        context={"logs": logs, "totalSeverity": tSeverity, "user": user},
    )


@router.get("/{product_id}/hosts")
async def get_hosts(
    request: Request,
    service: ProductServiceDep,
    plugin_service: PluginServiceDep,
    product_id: UUID,
):
    selected = request.session.get("finding-selected")
    if selected:
        selected: dict = json.loads(selected)
        for k in selected.keys():
            if selected[k] is None:
                selected[k] = []
    else:
        selected = {}
    hosts = await service.get_hosts(product_id)
    plugins = await plugin_service.get_all_activated()

    status = [
        {
            "value": v,
            "label": v.title(),
            "selected": v in selected.get("status", []),
        }
        for v in ("NEW", "OPEN", "CLOSED", "EXAMPTION")
    ]

    severity = [
        {"value": v, "label": v.title(), "selected": v in selected.get("severity", [])}
        for v in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
    ]

    plugins_process = [
        {
            "value": str(pl.id),
            "label": pl.name.title(),
            "selected": str(pl.id) in selected.get("plugin_id", []),
        }
        for pl in plugins
    ]

    hosts_process = [
        {"value": host, "label": host, "selected": host in selected.get("host", [])}
        for host in hosts
    ]

    data = {
        "plugins": plugins_process,
        "hosts": hosts_process,
        "status": status,
        "severity": severity,
    }

    # request.session.update({"finding-filters": json.dumps(data)})

    return templates.TemplateResponse(
        request,
        "pages/product/response/findingFilter.html",
        data,
    )


@router.post("/{product_id}/finding-filters")
async def filter_findings(
    request: Request, product_id: UUID, filters: Annotated[FindingFiltersSchema, Form()]
):
    request.session.update({"finding-selected": json.dumps(filters.model_dump())})
    return templates.TemplateResponse(
        request,
        "empty.html",
        headers={"HX-Trigger": "reload-findings"},
    )
