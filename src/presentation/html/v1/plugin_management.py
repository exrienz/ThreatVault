from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse

from src.application.dependencies.service_dependency import PluginServiceDep
from src.application.schemas.finding import FindingUploadSchema
from src.application.services.fileupload_service import (
    HAUploadService,
    VAUploadService,
)
from src.presentation.dependencies import PermissionChecker

from ..utils import templates

router = APIRouter(
    prefix="/setting/plugin",
    tags=["plugin-config"],
    dependencies=[Depends(PermissionChecker(["manage-plugin:full"]))],
)


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
):
    return templates.TemplateResponse(
        request,
        "pages/plugin_management/index.html",
    )


@router.get("/list", response_class=HTMLResponse)
async def get_all(request: Request, service: PluginServiceDep):
    plugins = await service.get_all()
    return templates.TemplateResponse(
        request,
        "pages/plugin_management/response/list.html",
        {
            "plugins": plugins,
        },
    )


@router.post("/create", response_class=HTMLResponse)
async def create(
    request: Request,
    service: PluginServiceDep,
    description: Annotated[str, Form()],
    config: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    active: Annotated[bool, Form()] = False,
    env: Annotated[str, Form()] = "VA",
):
    if env not in {"VA", "HA"}:
        raise
    data = {
        "description": description,
        "config": config,
        "is_active": active,
        "env": env,
    }
    await service.create(data, file)
    return templates.TemplateResponse(
        request,
        "empty.html",
        headers={"HX-Trigger": "reload-plugin-list"},
    )


@router.get("/verify/{plugin_id}", response_class=HTMLResponse)
async def verification_page(
    request: Request,
    plugin_id: UUID,
):
    return templates.TemplateResponse(
        request, "pages/plugin_management/form/verify.html", {"plugin_id": plugin_id}
    )


@router.post("/verify/{plugin_id}", response_class=HTMLResponse)
async def plugin_verification(
    request: Request,
    service: PluginServiceDep,
    plugin_id: UUID,
    file: Annotated[UploadFile, File()],
    use_to_verify: Annotated[bool, Form()] = False,
    type_: str | None = None,
):
    plugin_info = await service.get_by_id(plugin_id)
    data = FindingUploadSchema(scan_date=datetime.now(), plugin=plugin_info.id)

    if type_ == "HA":
        fileupload = HAUploadService(
            service.repository.session, file, plugin_info.id, data
        )
    else:
        fileupload = VAUploadService(
            service.repository.session, file, plugin_info.id, data
        )

    verified = await fileupload.plugin_verification()
    headers = {}
    if use_to_verify:
        await service.update(plugin_id, {"verified": verified})
        headers = {"HX-Trigger": "reload-plugin-list"}
    # TODO: Provide detail error, so that user can fix their code
    return templates.TemplateResponse(
        request,
        "pages/plugin_management/response/verify.html",
        {"verified": verified},
        headers=headers,
    )


@router.get("/edit/{plugin_id}", response_class=HTMLResponse)
async def edit_plugin_page(
    request: Request,
    plugin_id: UUID,
    service: PluginServiceDep,
):
    plugin = await service.get_by_id(plugin_id)
    return templates.TemplateResponse(
        request, "pages/plugin_management/form/edit.html", {"plugin": plugin}
    )


@router.put("/edit/{plugin_id}", response_class=HTMLResponse)
async def edit_plugin(
    request: Request,
    plugin_id: UUID,
    service: PluginServiceDep,
    description: Annotated[str, Form()],
    config: Annotated[str, Form()],
    active: Annotated[bool, Form()] = False,
    file: Annotated[UploadFile | None, File()] = None,
):
    data = {"description": description, "config": config, "is_active": active}
    await service.update(plugin_id, data, file)
    return templates.TemplateResponse(
        request,
        "empty.html",
        headers={"HX-Trigger": "reload-plugin-list"},
    )
