from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from src.application.services import EnvService, ProjectManagementService
from src.presentation.dependencies import PermissionChecker

from ..utils import templates

router = APIRouter(
    prefix="/project-management",
    tags=["Project Management"],
    dependencies=[
        Depends(
            PermissionChecker(
                [
                    "project-management:view",
                    "project-management:create",
                    "project-management:delete",
                ]
            )
        ),
    ],
)

projectService = Annotated[ProjectManagementService, Depends()]


@router.get("", response_class=HTMLResponse)
async def project_management(
    request: Request, service: projectService, type_: str | None = "VA"
):
    if type_ not in {"VA", "HA"}:
        raise
    projects = await service.get_all_by_filters({"type_": type_})
    assessment_map = {"VA": "VAPT", "HA": "Compliance"}
    return templates.TemplateResponse(
        request,
        "pages/project_management/index.html",
        {
            "projects": projects,
            "assessment_type": assessment_map.get(type_),
            "type_": type_,
        },
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
    if environment_name == "all":
        await service.create_product_both_env(project_id, name)
    else:
        await service.create_product(project_id, environment_name, name)

    project = await service.get_project_by_id(project_id)
    return templates.TemplateResponse(
        request,
        "pages/project_management/response/create_product.html",
        context={
            "project": project,
            "name": name,
            "environment_name": environment_name,
        },
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
