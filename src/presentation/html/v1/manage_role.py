from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from src.application.dependencies.service_dependency import RoleServiceDep
from src.domain.entity.user_access import Role
from src.presentation.dependencies import PermissionChecker

from ..utils import templates

router = APIRouter(
    prefix="/manage-role",
    tags=["manage-role"],
    dependencies=[Depends(PermissionChecker(admin_only=True))],
)


@router.get("", response_class=HTMLResponse)
async def get_index_page(
    request: Request,
    service: RoleServiceDep,
):
    roles = await service.get_all_with_permissions()
    return templates.TemplateResponse(
        request,
        "pages/manage_role/index.html",
        {"roles": roles, "cannot_update": service._cannot_update_list()},
    )


@router.get("/edit-form/{role_id}", response_class=HTMLResponse)
async def get_edit_form(
    request: Request,
    service: RoleServiceDep,
    role_id: UUID,
):
    await service.can_update(role_id)
    role = await service.get_one_with_permissions({Role.id: role_id})
    if role is None:
        raise
    permissions = await service.get_all_permissions()
    return templates.TemplateResponse(
        request,
        "pages/manage_role/form/edit.html",
        {"role": role, "permissions": permissions},
    )


@router.patch("/{role_id}")
async def edit_role(
    request: Request,
    service: RoleServiceDep,
    role_id: UUID,
    required_project_access: Annotated[bool, Form()],
    permissions: Annotated[list[UUID] | None, Form()] = None,
):
    await service.can_update(role_id)
    await service.update_role(
        role_id, {"required_project_access": required_project_access}
    )
    await service.update_permissions(role_id, permissions or [])
    role = await service.get_one_with_permissions({Role.id: role_id})
    return templates.TemplateResponse(
        request,
        "pages/manage_role/response/edit.html",
        {"role": role},
    )


# @router.post("", response_class=HTMLResponse)
# async def manage_owner(
#     request: Request,
#     service: ProductServiceDep,
#     product_id: Annotated[UUID, Form()],
#     user_id: Annotated[UUID, Form()],
#     granted: Annotated[bool, Form()] = True,
# ):
#     access = await service.manage_product_access(product_id, user_id, granted)
#     return templates.TemplateResponse(
#         request,
#         "pages/manage_owner/response/toggle_access.html",
#         {"access": access, "granted": granted},
#         headers={"HX-Trigger": "resetOwnerForm"},
#     )
