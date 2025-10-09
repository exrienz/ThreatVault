import io
import json
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import PositiveInt
from sqlalchemy.ext.asyncio import AsyncSession
from xhtml2pdf import pisa

# import weasyprint
from src.application.dependencies import (
    FindingServiceDep,
    LogServiceDep,
    PluginServiceDep,
    ProductServiceDep,
    ProjectManagementServiceDep,
    UserServiceDep,
)
from src.application.schemas.finding import (
    FindingActionInternalSchema,
    FindingActionRequestSchema,
    FindingFiltersSchema,
    FindingUploadSchema,
    ManualFindingUploadSchema,
)
from src.application.services.fileupload_service import (
    UploadFileServiceGeneral,
)
from src.application.utils.generate_pdf import generate_doughnut_url
from src.domain.constant import FnStatusEnum, SeverityEnum
from src.infrastructure.database.session import get_session
from src.presentation.dependencies import PermissionChecker

from ..utils import templates

router = APIRouter(prefix="/product", tags=["product"])


@router.get("/{product_id}", response_class=HTMLResponse)
async def get_product(
    request: Request,
    service: ProductServiceDep,
    log_service: LogServiceDep,
    plugin_service: PluginServiceDep,
    finding_service: FindingServiceDep,
    product_id: UUID,
):
    product = await service.get_by_id(product_id)
    hosts = await service.get_hosts(product_id)
    if product is None:
        raise HTTPException(404, "Project is not exists!")
    logs = await log_service.get_by_product_id(product_id)
    report_dates = await log_service.get_available_date_by_product(product_id)
    # TODO: Optimize, split fileupload view
    plugins = await plugin_service.get_all_activated(
        {"env": product.environment.project.type_}
    )
    labels = await finding_service.get_labels(product_id)
    tSeverity = 1
    if logs:
        tSeverity = logs.tCritical + logs.tHigh + logs.tMedium + logs.tLow

    return templates.TemplateResponse(
        request,
        "pages/product/index.html",
        {
            "product": product,
            "logs": logs,
            "totalSeverity": tSeverity,
            "plugins": plugins,
            "host_list": hosts,
            "report_dates": report_dates,
            "labels": labels,
        },
    )


@router.get("/{product_id}/table-view")
async def swap_finding_table_view(
    request: Request,
    product_id: UUID,
    view: str = "default",
):
    return templates.TemplateResponse(
        request,
        "pages/product/component/tables/index.html",
        {"view": view, "product_id": product_id},
    )


@router.get("/{product_id}/findings", response_class=HTMLResponse)
async def get_findings(
    request: Request,
    services: ProductServiceDep,
    finding_service: FindingServiceDep,
    product_id: UUID,
    view: str = "default",
    severity: SeverityEnum = SeverityEnum.CRITICAL,
    page: PositiveInt = 1,
    host: Annotated[list[str] | None, Query()] = None,
    status: Annotated[list[str] | None, Query()] = None,
    severity_filter: Annotated[list[str] | None, Query()] = None,
    plugin_id: Annotated[list[UUID] | None, Query()] = None,
    label: Annotated[list[str] | None, Query()] = None,
):
    filters = {
        "plugin_id": plugin_id,
        "status": status,
        "severity": severity_filter,
        "host": host,
        "label": label,
    }

    fn_dict = {
        "assets": [finding_service.get_group_by_assets, (product_id, page, filters)],
        "slaBreach": [finding_service.get_breached_findings, (product_id, severity)],
    }
    fn = fn_dict.get(
        view,
        [finding_service.get_group_by_severity_status, (product_id, page, filters)],
    )

    product = await services.get_by_id(product_id)
    product_type = None
    if product:
        product_type = product.environment.project.type_

    data = await fn[0](*fn[1])
    return templates.TemplateResponse(
        request,
        "pages/product/response/findings.html",
        {
            "product_id": product_id,
            "view": view,
            "severity": severity,
            "product_type": product_type,
            **data,
        },
    )


@router.post(
    "/{product_id}/action",
    dependencies=[Depends(PermissionChecker(["finding:action"]))],
)
async def finding_action(
    request: Request,
    product_id: UUID,
    data: Annotated[FindingActionRequestSchema, Form()],
    finding_service: FindingServiceDep,
    log_service: LogServiceDep,
):
    try:
        status = FnStatusEnum(data.action.upper())
    except Exception:
        status = FnStatusEnum.OTHERS
        data.remark += f"\n System: {data.action}"
        data.delay_untill = None

    if data.delay_untill and status != FnStatusEnum.OTHERS:
        data.remark += f"\n Remediation Date: {data.delay_untill.strftime('%d-%m-%Y')}"

    internal = FindingActionInternalSchema(status=status.value, **data.model_dump())

    filters = {
        "hosts": data.hosts,
        "current_status": data.current_status,
    }
    await finding_service.update(data.finding_name_id, filters, internal)

    await log_service.calculate(product_id, datetime.now())
    return templates.TemplateResponse(
        request,
        "empty.html",
        headers={"HX-Trigger": "reload-findings, reload-stats"},
    )


@router.post(
    "/{product_id}/upload",
    response_class=HTMLResponse,
    dependencies=[Depends(PermissionChecker(["finding:create"]))],
)
async def upload_file(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: LogServiceDep,
    backgound_tasks: BackgroundTasks,
    product_id: UUID,
    formFile: Annotated[list[UploadFile], File()],
    scan_date: Annotated[datetime, Form()],
    plugin: Annotated[UUID, Form()],
    process_new_finding: Annotated[bool, Form()] = False,
    sync_update: Annotated[bool, Form()] = False,
    overwrite: Annotated[bool, Form()] = False,
    label: Annotated[str | None, Form()] = None,
    new_label: Annotated[str | None, Form()] = None,
):
    """
    TODO:
        - All the error handling
        - Sync Update
    """
    label = (new_label or label or "").strip() or None
    data_dict = {
        "scan_date": scan_date,
        "plugin": plugin,
        "process_new_finding": process_new_finding,
        "sync_update": sync_update,
        "overwrite": overwrite,
        "label": label,
    }
    data = FindingUploadSchema(**data_dict)
    uploader = UploadFileServiceGeneral(session, formFile, product_id, data)
    # uploader = await UploadFileServiceGeneral(
    #     session, formFile, product_id, data
    # ).uploader()
    #
    # try:
    #     await uploader.scan_date_validation()
    #     await uploader.plugin_verification()
    # except pl.exceptions.PolarsError:
    #     raise InvalidInput("Plugin didn't match the file uploaded!")
    #
    # async def bg_upload():
    #     await uploader.upload_background()
    #     await service.calculate(product_id, uploader.scan_date)
    #
    # backgound_tasks.add_task(bg_upload)

    fileupload = await uploader.upload()
    logs = await service.calculate(product_id, fileupload.scan_date)
    tSeverity = 1
    if logs:
        tSeverity = logs.tCritical + logs.tHigh + logs.tMedium + logs.tLow
    else:
        tSeverity = 1
    filenames = [file.filename for file in uploader.files]
    return templates.TemplateResponse(
        request,
        "pages/product/response/fileupload.html",
        headers={"HX-Trigger": "reload-findings, reload-stats"},
        context={
            "logs": logs,
            "totalSeverity": tSeverity,
            "filename": filenames,
        },
    )


@router.post(
    "/{product_id}/upload/manual",
    dependencies=[Depends(PermissionChecker(["finding:create"]))],
)
async def manual_upload(
    request: Request,
    service: FindingServiceDep,
    log_service: LogServiceDep,
    product_id: UUID,
    data: Annotated[ManualFindingUploadSchema, Form()],
):
    await service.manual_upload(
        {"name": data.finding_name, "product_id": product_id},
        data.model_dump(exclude={"finding_name"}),
    )
    logs = await log_service.calculate(
        product_id, data.finding_date.replace(hour=0, minute=0, second=0, microsecond=0)
    )
    if logs:
        tSeverity = logs.tCritical + logs.tHigh + logs.tMedium + logs.tLow
    else:
        tSeverity = 1
    return templates.TemplateResponse(
        request,
        "pages/product/response/fileupload.html",
        headers={"HX-Trigger": "reload-findings, reload-stats"},
        context={"logs": logs, "totalSeverity": tSeverity},
    )


@router.get("/{product_id}/stats", response_class=HTMLResponse)
async def product_stats(
    request: Request,
    product_id: UUID,
    service: LogServiceDep,
    product_service: ProductServiceDep,
    project_service: ProjectManagementServiceDep,
):
    product = await product_service.get_by_id(product_id)
    if product is None:
        raise
    project = await project_service.get_project_by_id(product.environment.project_id)
    if project is None:
        raise
    logs = await service.get_by_product_id(product_id)
    return templates.TemplateResponse(
        request,
        f"pages/product/response/{project.type_.lower()}_stats.html",
        {"logs": logs},
    )


@router.get(
    "/{product_id}/user-permissions",
    dependencies=[Depends(PermissionChecker(["finding:action"]))],
)
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


@router.post(
    "/{product_id}/user-permission",
    dependencies=[Depends(PermissionChecker(["finding:action"]))],
)
async def toggle_user_permission(
    request: Request,
    service: ProductServiceDep,
    product_id: UUID,
    user_id: Annotated[UUID, Form()],
    granted: Annotated[bool, Form()] = True,
):
    await service.manage_product_access(product_id, user_id, granted)


@router.post(
    "/{product_id}/generate-api-key",
    dependencies=[Depends(PermissionChecker(["finding:action"]))],
)
async def generate_api_key(
    request: Request, service: ProductServiceDep, product_id: UUID
):
    product = await service.generate_api_key(product_id)
    return templates.TemplateResponse(
        request, "pages/product/response/tokenGeneration.html", {"product": product}
    )


@router.get("/{product_id}/escalation")
async def get_escalation_list(
    request: Request,
    service: ProductServiceDep,
    product_id: UUID,
):
    escalated, allowed = await service.get_escalation_options(product_id)
    return templates.TemplateResponse(
        request,
        "pages/product/response/escalation.html",
        {"escalated": escalated, "allowed": allowed},
    )


@router.post(
    "/{product_id}/escalation",
    dependencies=[Depends(PermissionChecker(["finding:action"]))],
)
async def escalation_list(
    request: Request,
    service: UserServiceDep,
    product_service: ProductServiceDep,
    product_id: UUID,
    user_ids: Annotated[list[UUID] | None, Form()] = None,
    weekly: Annotated[bool, Form()] = False,
    monthly: Annotated[bool, Form()] = False,
):
    await product_service.update_escalation(
        product_id, user_ids, monthly=monthly, weekly=weekly
    )
    return templates.TemplateResponse(
        request,
        "pages/product/response/escalationSuccess.html",
    )


@router.get(
    "/{product_id}/revert",
    dependencies=[Depends(PermissionChecker(["finding:revert"]))],
)
async def revert_modal(
    request: Request,
    service: LogServiceDep,
    finding_service: FindingServiceDep,
    product_id: UUID,
):
    current = await service.get_by_product_id(product_id)
    prev = await service.get_prev_by_product_id(product_id)
    keys = ["tNew", "tOpen", "tClosed", "tExemption", "tOthers"]
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


# Deprecated
@router.post(
    "/{product_id}/revert",
    dependencies=[Depends(PermissionChecker(["finding:action"]))],
)
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
        if logs.uploader_id:
            user = await user_service.get_by_id(logs.uploader_id)

    return templates.TemplateResponse(
        request,
        "pages/product/response/fileupload.html",
        headers={"HX-Trigger": "reload-findings"},
        context={"logs": logs, "totalSeverity": tSeverity, "user": user},
    )


# Deprecated
@router.get("/{product_id}/finding-filters")
async def get_hosts(
    request: Request,
    service: ProductServiceDep,
    plugin_service: PluginServiceDep,
    product_id: UUID,
):
    selected = request.session.get("finding-selected")
    if selected:
        if not isinstance(selected, dict):
            selected = json.loads(selected)
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
        for v in ("NEW", "OPEN", "CLOSED", "EXEMPTION")
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

    return templates.TemplateResponse(
        request,
        "pages/product/response/findingFilter.html",
        data,
    )


# Deprecated
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


@router.get("/{product_id}/pic-list")
async def get_pic_list(
    request: Request,
    service: ProductServiceDep,
    product_id: UUID,
):
    users = await service.get_owners_by_product_id(product_id)
    return templates.TemplateResponse(
        request,
        "pages/finding/component/pic.html",
        {
            "data": users,
        },
    )


# TODO: Handle for large data
@router.get("/{product_id}/report")
async def download_report(
    request: Request,
    service: ProductServiceDep,
    log_service: LogServiceDep,
    finding_service: FindingServiceDep,
    product_id: UUID,
    date: datetime | None = None,
    type_: str | None = "VA",
):
    if date is None:
        date = datetime.now()
    if type_ != "VA":
        raise HTTPException(404)

    month, year = date.month, date.year

    product = await service.get_by_id(product_id)
    if product is None:
        raise

    curr_log = await log_service.get_by_product_id(product_id)
    prev_log = await log_service.get_by_date_filter(product_id, year, month)

    curr_url = generate_doughnut_url(curr_log, "VA")
    prev_url = generate_doughnut_url(prev_log, "VA")

    hosts = await service.get_hosts(product_id)

    findings, evidences_dict = await finding_service.report_findings(product_id)
    res = templates.TemplateResponse(
        request,
        "pages/product/report_template.html",
        {
            "product": product,
            "curr_log": curr_log,
            "prev_log": prev_log,
            "prev_url": prev_url,
            "curr_url": curr_url,
            "hosts": hosts,
            "findings": findings,
            "evidences_dict": evidences_dict,
        },
    )

    def iter_csv():
        buf = io.BytesIO()
        pisa.CreatePDF(src=bytes(res.body), dest=buf)
        buf.seek(0)
        yield from buf

    return StreamingResponse(
        iter_csv(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={product.name}-report.pdf"},
    )
