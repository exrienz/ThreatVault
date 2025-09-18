from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from src.application.dependencies import (
    ProductServiceDep,
    ProjectManagementServiceDep,
    UserServiceDep,
)
from src.presentation.dependencies import PermissionChecker

from ..utils import templates

router = APIRouter(
    prefix="/manage-owner",
    tags=["manage-owner"],
    dependencies=[Depends(PermissionChecker(["manage-owner:full"]))],
)


@router.get("", response_class=HTMLResponse)
async def get_index_page(
    request: Request,
    project_service: ProjectManagementServiceDep,
    user_service: UserServiceDep,
    product_service: ProductServiceDep,
):
    projects = await project_service.get_project_extended()
    users = await user_service.get_all(
        filters={"role": "Owner", "active": True}, pagination=False
    )
    products = await product_service.get_products_with_owner()
    products_by_id = {product.id: product for product in products}
    return templates.TemplateResponse(
        request,
        "pages/manage_owner/index.html",
        {
            "projects": projects,
            "users": users,
            "owners": products_by_id,
        },
    )


@router.post("", response_class=HTMLResponse)
async def manage_owner(
    request: Request,
    service: ProductServiceDep,
    product_id: Annotated[UUID, Form()],
    user_id: Annotated[UUID, Form()],
    granted: Annotated[bool, Form()] = True,
):
    access, product, user = await service.manage_product_access(
        product_id, user_id, granted
    )
    return templates.TemplateResponse(
        request,
        "pages/manage_owner/response/toggle_access.html",
        {
            "access": access,
            "granted": granted,
            "product": product,
            "user": user,
        },
        headers={"HX-Trigger": "resetOwnerForm"},
    )
