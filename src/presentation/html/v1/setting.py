from typing import Annotated

from fastapi import APIRouter, Form, Request

from src.application.dependencies.service_dependency import (
    GlobalServiceDep,
    OpenAIServiceDep,
)
from src.application.schemas.settings import GlobalConfigSchema

from ..utils import templates

router = APIRouter(prefix="/setting", tags=["Setting"])


@router.get("")
async def get_index_page(request: Request, service: GlobalServiceDep):
    data = await service.get()
    # jobs = scheduler.scheduler.get_jobs()
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
        {"data": config, "updated": True},
    )


@router.get("/model-list")
async def get_llm_models_list(
    request: Request,
    service: OpenAIServiceDep,
    llm_url: str,
    llm_api_key: str,
):
    curr_model = await service.get_current_model()
    models = await service.get_models(llm_url, llm_api_key)
    return templates.TemplateResponse(
        request,
        "pages/setting/model_search.html",
        {"models": models, "curr_model": curr_model},
    )
