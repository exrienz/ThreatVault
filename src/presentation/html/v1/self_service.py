from typing import Annotated

from fastapi import APIRouter, Form, Request

from src.application.dependencies.service_dependency import (
    UserServiceDep,
)
from src.application.middlewares.user_context import get_current_user_id
from src.application.schemas.settings import UserResetPasswordSchema
from src.config import sidebar_items

from ..utils import templates

router = APIRouter(prefix="/self-service", tags=["Self-Service"])


@router.get("")
async def get_index_page(request: Request, service: UserServiceDep):
    user_id = get_current_user_id()
    if user_id is None:
        raise
    user = await service.get_by_id(user_id)
    return templates.TemplateResponse(
        request,
        "pages/user_setting/index.html",
        {"sidebarItems": sidebar_items, "user": user},
    )


@router.delete("/user")
async def delete_current_user(request: Request, service: UserServiceDep):
    user_id = get_current_user_id()
    if user_id is None:
        raise
    await service.delete(user_id)


@router.post("/reset-password")
async def reset_password(
    request: Request,
    service: UserServiceDep,
    data: Annotated[UserResetPasswordSchema, Form()],
):
    res = {"error": False}
    try:
        await service.reset_password(data)
    except Exception:
        res["error"] = True
    return templates.TemplateResponse(
        request, "pages/user_setting/response/resetPassword.html", res
    )
