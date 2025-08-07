from fastapi import APIRouter

from src.presentation.api.v1.router import router as V1_ROUTER

router = APIRouter(prefix="/api")
router.include_router(V1_ROUTER)
