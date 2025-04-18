from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from src.application.services import EnvService, ProjectManagementService
from src.config import sidebar_items

from ..utils import templates

router = APIRouter(prefix="/project-management", tags=["Project Management"])

projectService = Annotated[ProjectManagementService, Depends()]


@router.get("/", response_class=HTMLResponse)
async def project_management(request: Request, service: projectService):
    projects = await service.get_project_extended()
    return templates.TemplateResponse(
        request,
        "pages/project_management/index.html",
        {"sidebarItems": sidebar_items, "projects": projects},
    )


@router.post("/", response_class=HTMLResponse)
async def create_project(
    request: Request,
    name: Annotated[str, Form()],
    project_type: Annotated[str, Form()],
    service: projectService,
):
    project = await service.create_project({"name": name, "type_": project_type})
    return templates.TemplateResponse(
        request,
        "pages/project_management/response/create_project.html",
        context={"project": project, "idx": 999},
    )


@router.delete("/", response_class=HTMLResponse)
async def delete_project(
    request: Request,
    project_id: UUID,
    service: projectService,
):
    projects = await service.delete_project(project_id)
    return templates.TemplateResponse(
        request,
        "pages/project_management/response/remove_project.html",
        context={"projects": projects, "project_id": project_id},
    )


@router.get("/environments")
async def get_environments(
    request: Request,
    project_id: UUID,
    # service: EnvService = Depends()
    service: Annotated[EnvService, Depends()],
):
    envs = await service.get_by_project_id(project_id)
    return templates.TemplateResponse(
        request,
        "pages/project_management/component/environment_select.html",
        {"envs": envs},
    )


@router.get("/products")
async def get_products(
    request: Request,
    service: projectService,
    project_id: UUID | None = None,
    environment_id: UUID | None = None,
):
    products = await service.get_product_by_project_id(project_id, environment_id)
    return templates.TemplateResponse(
        request,
        "pages/project_management/component/product_select.html",
        {"products": products},
    )


@router.post("/product", response_class=HTMLResponse)
async def create_product(
    request: Request,
    name: Annotated[str, Form()],
    project_id: Annotated[UUID, Form()],
    environment_name: Annotated[str, Form()],
    service: projectService,
):
    product = await service.create_product(project_id, environment_name, name)
    return templates.TemplateResponse(
        request,
        "pages/project_management/response/create_product.html",
        context={"product": product},
    )


@router.delete("/product")
async def delete_product(
    request: Request,
    product_id,
    # service: ProjectManagementService = Depends()
    service: projectService,
):
    await service.delete_product(product_id)
    return templates.TemplateResponse(
        request,
        "pages/project_management/response/remove_product.html",
        context={"product_id": product_id},
    )
