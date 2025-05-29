from fastapi import APIRouter, Request

from src.presentation.html.v1 import v1_router

router = APIRouter()


@router.get("/ping", status_code=200)
async def ping(request: Request):
    return "ok"


router.include_router(v1_router)
