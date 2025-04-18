from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

import pytz
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import PositiveInt
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dependencies import (
    FindingServiceDep,
    GlobalServiceDep,
    LogServiceDep,
    PluginServiceDep,
    ProductServiceDep,
)
from src.application.dependencies.service_dependency import (
    TokenServiceDep,
    UserServiceDep,
)
from src.application.schemas.finding import ManualFindingUploadSchema
from src.application.services import FileUploadService, PluginService
from src.config import sidebar_items
from src.domain.constant import FnStatusEnum, SeverityEnum
from src.infrastructure.database.session import get_session

from ..utils import templates

router = APIRouter(prefix="/product", tags=["product"])


# TODO: Fix thisindex
@router.get("/{product_id}", response_class=HTMLResponse)
async def get_product(
    request: Request,
    service: ProductServiceDep,
    log_service: LogServiceDep,
    plugin_service: PluginServiceDep,
    tokenService: TokenServiceDep,
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
    global_service: GlobalServiceDep,
    product_id: UUID,
    page: PositiveInt = 1,
):
    findings = await finding_service.get_group_by_severity_status(product_id, page)
    sla = await global_service.get()
    sla_mapping = {}
    # TODO: Optimize this
    for finding in findings.data:
        severity: SeverityEnum = finding[2]
        finding_date: datetime = finding[5]
        try:
            sla_val = getattr(sla, "sla_" + severity.value.lower())
        except:  #  noqa: E722
            sla_val = 10
        sla_mapping[finding[0]] = (
            finding_date + timedelta(sla_val) - datetime.now(pytz.utc)
        ).days
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
    plugin: Annotated[str, Form()],
    formFile: Annotated[UploadFile, File()],
    process_new_finding: Annotated[bool, Form()] = False,
    sync_update: Annotated[bool, Form()] = False,
):
    """
    TODO:
        - All the error handling
        - Sync Update
    """
    # fn = plugin_service.plugin_import(self.plugin, "builtin/nessus.py")
    plugin_fn = PluginService.plugin_import(plugin.split("/")[-1], f"{plugin}.py")
    fileupload = FileUploadService(
        session,
        formFile,
        plugin_fn,
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
