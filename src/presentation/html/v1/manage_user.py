import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from pydantic import PositiveInt

from src.application.dependencies import RoleServiceDep, UserServiceDep
from src.application.schemas import UserUpdateSchema
from src.presentation.dependencies import PermissionChecker

from ..utils import templates

router = APIRouter(
    prefix="/manage-user",
    tags=["user"],
    dependencies=[Depends(PermissionChecker(["manage-user:full"]))],
)


# TODO: move to schemas
def list_users_req(
    email: str | None = None,
    role: str | None = None,
    active: bool | str | None = None,
) -> dict[str, str | bool]:
    res: dict[str, str | bool] = {}
    if email is not None:
        res["email"] = email
    if role is not None:
        res["role"] = role
    if active is not None and active != "":
        res["active"] = active == "true"
    return res


@router.get("/", response_class=HTMLResponse)
async def get_users(
    request: Request,
):
    return templates.TemplateResponse(
        request,
        "pages/manage_user/index.html",
    )


@router.get("/list", response_class=HTMLResponse)
async def get_list_users(
    request: Request,
    service: UserServiceDep,
    filters: Annotated[dict, Depends(list_users_req)],
    page: PositiveInt = 1,
):
    users = await service.get_all(page, filters)
    return templates.TemplateResponse(
        request,
        "pages/manage_user/response/list.html",
        {"users": users, "query": json.dumps(filters)},
    )


@router.get("/user/{user_id}", response_class=HTMLResponse)
async def get_user_detail(
    request: Request,
    service: UserServiceDep,
    role_service: RoleServiceDep,
    user_id: UUID,
):
    user = await service.get_by_id(user_id)
    roles = await role_service.get_all()
    projects = await service.get_accessible_project(user_id)
    return templates.TemplateResponse(
        request,
        "pages/manage_user/response/user_detail.html",
        {
            "user": user,
            "roles": roles,
            "projects": projects,
        },
    )


@router.put(
    "/user/{user_id}",
    response_class=HTMLResponse,
    dependencies=[Depends(PermissionChecker(admin_only=True))],
)
async def update_user(
    request: Request,
    service: UserServiceDep,
    data: Annotated[UserUpdateSchema, Form()],
    user_id: UUID,
):
    dct = data.model_dump()
    await service.update(user_id, dct)
    return templates.TemplateResponse(
        request,
        "pages/manage_user/response/update.html",
    )
