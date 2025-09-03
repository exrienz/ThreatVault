from fastapi import APIRouter

router = APIRouter(prefix="/cve", tags=["CVE"])


# @router.get("/recalculate", response_class=HTMLResponse)
# async def recalculate_cve(request: Request, background: BackgroundTasks):
#     # background.add_task(service.calculate_priority, False)
#     background.add_task(CVEService.generate_priority)
