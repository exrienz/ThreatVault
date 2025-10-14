import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from pydantic import PositiveInt

from src.application.dependencies import RoleServiceDep, UserServiceDep
from src.application.schemas import UserUpdateSchema
from src.application.schemas.auth import ExternalUserRegisterSchema
from src.application.security.oauth2.okta_sync_users import OKTAExternalService
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
    role_service: RoleServiceDep,
):
    roles = await role_service.get_all()
    return templates.TemplateResponse(
        request, "pages/manage_user/index.html", {"roles": roles}
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


@router.get("/list/external", response_class=HTMLResponse)
async def get_list_external_users(
    request: Request,
    service: UserServiceDep,
    okta_service: Annotated[OKTAExternalService, Depends()],
    filters: Annotated[dict, Depends(list_users_req)],
    page: PositiveInt = 1,
):
    data = await okta_service.get_users(filters.get("email"), page)
    users = data.get("users")
    emails = {usr.get("email") for usr in users}
    existing_user = await service.get_by_emails(list(emails))
    exists = {}
    for usr in existing_user:
        exists[usr.email] = usr
    return templates.TemplateResponse(
        request,
        "pages/manage_user/response/oidc_list.html",
        {"data": data, "page": page, "existing_user": exists},
    )


@router.post(
    "/user/external",
    response_class=HTMLResponse,
    dependencies=[Depends(PermissionChecker(admin_only=True))],
)
async def add_from_external(
    request: Request,
    service: UserServiceDep,
    data: Annotated[ExternalUserRegisterSchema, Form()],
):
    data_dict = data.model_dump()
    data_dict["active"] = True
    await service.create(data_dict)
    user = await service.get_by_emails([data.email])
    return templates.TemplateResponse(
        request,
        "pages/manage_user/response/oidc_add.html",
        {"user": user[0]},
    )


@router.get(
    "/user/{user_id}",
    response_class=HTMLResponse,
    dependencies=[Depends(PermissionChecker(admin_only=True))],
)
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
