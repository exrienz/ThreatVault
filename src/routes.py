from fastapi import APIRouter

from src.presentation.html.v1 import v1_router

router = APIRouter()


@router.get("/ping", status_code=200)
async def ping():
    return "ok"


router.include_router(v1_router)
