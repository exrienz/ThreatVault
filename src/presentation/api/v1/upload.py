from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dependencies.service_dependency import (
    LogServiceDep,
    PluginServiceDep,
)
from src.application.schemas.finding import FindingUploadSchema
from src.application.services.fileupload_service import (
    UploadFileServiceGeneral,
)
from src.infrastructure.database.session import get_session

router = APIRouter(prefix="/upload", tags=["File Upload_API"])


@router.post("")
async def upload_file(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    service: LogServiceDep,
    plugin_service: PluginServiceDep,
    product_id: UUID,
    type_: str,
    formFile: Annotated[UploadFile, File()],
    scan_date: Annotated[datetime, Form()],
    plugin_name: Annotated[UUID, Form()],
    process_new_finding: Annotated[bool, Form()] = False,
    sync_update: Annotated[bool, Form()] = False,
    overwrite: Annotated[bool, Form()] = False,
):
    plugin = await plugin_service.get_by_filter({"name": plugin_name, "env": type_})
    if plugin is None:
        raise HTTPException(400, f"{plugin_name} for {type_} does not exists")
    data_dict = {
        "scan_date": scan_date,
        "plugin": plugin,
        "process_new_finding": process_new_finding,
        "sync_update": sync_update,
        "overwrite": overwrite,
    }
    data = FindingUploadSchema(**data_dict)

    uploader = UploadFileServiceGeneral(session, formFile, product_id, data)
    fileupload = await uploader.upload()
    await fileupload.upload()
    await service.calculate(product_id, fileupload.scan_date)
