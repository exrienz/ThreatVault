from fastapi import APIRouter, BackgroundTasks, Request
from fastapi.responses import HTMLResponse

from src.application.dependencies.service_dependency import (
    CVEServiceDep,
)
from src.application.services.cve_services import CVEService

router = APIRouter(prefix="/cve", tags=["CVE"])


# @router.get("/recalculate", response_class=HTMLResponse)
# async def recalculate_cve(request: Request, background: BackgroundTasks):
#     # background.add_task(service.calculate_priority, False)
#     background.add_task(CVEService.generate_priority)
