from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, Request

from src.application.dependencies import TokenServiceDep

from ..utils import templates

router = APIRouter(prefix="/manage-api", tags=["manage-api"])


@router.get("")
async def get_index_page(
    request: Request,
    service: TokenServiceDep,
):
    data = await service.get_all()
    return templates.TemplateResponse(
        request,
        "pages/manage_api/index.html",
        {"data": data},
    )


@router.post("/generate")
async def generate_user_api_key(
    request: Request,
    service: TokenServiceDep,
    name: Annotated[str, Form()],
):
    data = await service.create(name)
    return templates.TemplateResponse(
        request, "pages/manage_api/component/row.html", {"api": data}
    )


@router.get("/{token_id}")
async def get_token(request: Request, service: TokenServiceDep, token_id: UUID):
    data = await service.get_by_id(token_id)
    if data is None:
        return
    return templates.TemplateResponse(
        request, "pages/manage_api/response/token.html", {"token": data.token}
    )


@router.delete("/{token_id}")
async def delete_token(request: Request, service: TokenServiceDep, token_id: UUID):
    await service.delete(token_id)
