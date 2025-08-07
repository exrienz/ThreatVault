from fastapi import APIRouter, Request

from src.presentation.router import router as presentation

router = APIRouter()


@router.get("/ping", status_code=200)
async def ping(request: Request):
    return "ok"


router.include_router(presentation)
