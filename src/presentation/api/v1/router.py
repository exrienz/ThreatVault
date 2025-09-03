from fastapi import APIRouter, Depends

from src.presentation.api.v1.chart import router as Charts
from src.presentation.api.v1.upload import router as Upload
from src.presentation.dependencies import verify_auth

router = APIRouter(prefix="", dependencies=[Depends(verify_auth)])
router.include_router(Charts)
router.include_router(Upload)
