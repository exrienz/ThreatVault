from typing import Annotated

from fastapi import APIRouter, Form, Request

from src.application.dependencies.service_dependency import (
    UserServiceDep,
)
from src.application.schemas.auth import UserResetPasswordSchema

from ..utils import templates

router = APIRouter(prefix="/setting", tags=["Self-Service"])


@router.get("/account")
async def get_index_page(
    request: Request,
    service: UserServiceDep,
):
    user = await service.get_me()
    return templates.TemplateResponse(
        request,
        "pages/user_setting/index.html",
        {
            "user": user,
        },
    )


@router.delete("/user")
async def delete_current_user(request: Request, service: UserServiceDep):
    await service.delete_me()


@router.post("/reset-password")
async def reset_password(
    request: Request,
    service: UserServiceDep,
    data: Annotated[UserResetPasswordSchema, Form()],
):
    await service.reset_password(data)
    return templates.TemplateResponse(
        request, "pages/user_setting/response/resetPassword.html"
    )
