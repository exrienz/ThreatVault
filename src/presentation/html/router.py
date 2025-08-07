from fastapi import APIRouter

from src.presentation.html.v1.router import v1_router

router = APIRouter(prefix="")
router.include_router(v1_router)
