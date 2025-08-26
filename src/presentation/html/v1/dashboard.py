import io
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse, StreamingResponse

from src.application.dependencies.service_dependency import (
    FindingServiceDep,
    ProjectManagementServiceDep,
)

from ..utils import templates

router = APIRouter(
    tags=["Dashboard"],
)


@router.get("/")
async def get_dashboard(
    request: Request,
    service: ProjectManagementServiceDep,
    type_: str | None = None,
):
    type_map = {"vapt": "VA", "compliance": "HA"}
    type_ = type_ if type_ else "vapt"
    projects = await service.get_all_with_logs(env=type_map.get(type_, "VA"))
    return templates.TemplateResponse(
        request,
        "pages/dashboard/index.html",
        {"projects": projects, "type": type_.upper()},
    )


@router.get("/project/{project_id}", response_class=HTMLResponse)
async def get_project_dashboard(
    request: Request,
    service: ProjectManagementServiceDep,
    project_id: UUID,
):
    project = await service.get_project_by_id(project_id)

    if project is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID({project_id}) cannot be found!",
        )

    prod_env = None
    nonprod_env = None
    for env in project.environment:
        if env.name == "production":
            prod_env = env
        else:
            nonprod_env = env

    return templates.TemplateResponse(
        request,
        "pages/dashboard/project.html",
        {
            "project": project,
            "prod_env": prod_env,
            "nonprod_env": nonprod_env,
        },
    )


@router.get("/project/{project_id}/export")
async def export_dashbord(
    request: Request,
    service: FindingServiceDep,
    project_service: ProjectManagementServiceDep,
    project_id: UUID,
):
    project = await project_service.get_one_by_id(project_id)
    df = await service.export_active_finding(project_id)

    def iter_csv():
        buf = io.StringIO()
        df.write_csv(buf)
        buf.seek(0)
        yield from buf

    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={project.name}-active-findings.csv"
        },
    )
