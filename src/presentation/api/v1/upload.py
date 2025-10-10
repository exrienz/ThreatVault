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
    Request,
    UploadFile,
)
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dependencies.service_dependency import (
    LogServiceDep,
    ProductServiceDep,
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
    product_service: ProductServiceDep,
    backgound_tasks: BackgroundTasks,
    product_id: UUID,
    formFile: Annotated[list[UploadFile], File()],
    plugin: Annotated[UUID, Form()],
    scan_date: Annotated[datetime | None, Form()] = None,
    process_new_finding: Annotated[bool, Form()] = True,
    sync_update: Annotated[bool, Form()] = False,
    label: Annotated[str | None, Form()] = None,
):
    product = await product_service.get_by_id(product_id)
    if product is None:
        raise HTTPException(400, f"Product with {product_id} does not exists!")
    label = (label or "").strip() or None
    data_dict = {
        "scan_date": scan_date if scan_date else datetime.now(),
        "plugin": plugin,
        "process_new_finding": process_new_finding,
        "sync_update": sync_update,
        "overwrite": False,
        "label": label,
    }
    data = FindingUploadSchema(**data_dict)
    uploader = await UploadFileServiceGeneral(
        session, formFile, product_id, data
    ).uploader()

    await uploader.upload()
    await service.calculate(product_id, uploader.scan_date)

    return JSONResponse(
        content="File uploaded and processed successfully.",  # noqa: E501
        status_code=200,
    )
