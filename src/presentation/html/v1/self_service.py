from fastapi import APIRouter, Request

from src.application.dependencies.service_dependency import (
    UserServiceDep,
)
from src.application.middlewares.user_context import get_current_user_id
from src.config import sidebar_items

from ..utils import templates

router = APIRouter(prefix="/self-service", tags=["Self-Service"])


@router.get("")
async def get_index_page(request: Request):
    return templates.TemplateResponse(
        request,
        "pages/user_setting/index.html",
        {"sidebarItems": sidebar_items},
    )


@router.delete("/user")
async def delete_current_user(request: Request, service: UserServiceDep):
    user_id = get_current_user_id()
    if user_id is None:
        raise
    await service.delete(user_id)
