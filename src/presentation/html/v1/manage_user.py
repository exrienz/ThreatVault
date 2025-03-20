from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from pydantic import PositiveInt

from src.application.services import UserService
from src.config import sidebar_items

from ..utils import templates

router = APIRouter(prefix="/manage-user", tags=["user"])


@router.get("/", response_class=HTMLResponse)
async def get_users(request: Request):
    return templates.TemplateResponse(
        request,
        "pages/manage_user/index.html",
        {
            "sidebarItems": sidebar_items,
        },
    )


def list_users_req(
    email: str | None = None,
    role: str | None = None,
    status: bool | None = None,
) -> dict:
    res = {}
    if email is not None:
        res["email"] = email
    if role is not None:
        res["role"] = role
    if status is not None:
        res["active"] = status
    return res


@router.get("/list", response_class=HTMLResponse)
async def get_list_users(
    request: Request,
    service: Annotated[UserService, Depends()],
    filters: Annotated[dict, Depends(list_users_req)],
    page: PositiveInt = 1,
):
    users = await service.get_all(page, filters)
    return templates.TemplateResponse(
        request,
        "pages/manage_user/response/list.html",
        {
            "users": users,
        },
    )
