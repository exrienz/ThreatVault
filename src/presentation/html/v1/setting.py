from typing import Annotated

from fastapi import APIRouter, Form, Request

from src.application.dependencies.service_dependency import (
    GlobalServiceDep,
)
from src.application.schemas.settings import GlobalConfigSchema

from ..utils import templates

router = APIRouter(prefix="/setting", tags=["Setting"])


@router.get("")
async def get_index_page(request: Request, service: GlobalServiceDep):
    data = await service.get()
    return templates.TemplateResponse(
        request,
        "pages/setting/index.html",
        {"data": data},
    )


@router.post("")
async def update_global_Setting(
    request: Request,
    service: GlobalServiceDep,
    data: Annotated[GlobalConfigSchema, Form()],
):
    config = await service.update(data.model_dump())
    return templates.TemplateResponse(
        request,
        "pages/setting/form.html",
        {"data": config},
    )
