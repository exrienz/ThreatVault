from fastapi import APIRouter

from src.presentation.api.router import router as API_ROUTER
from src.presentation.html.router import router as HTML_ROUTER

router = APIRouter(prefix="")
router.include_router(HTML_ROUTER, include_in_schema=False)
router.include_router(API_ROUTER)
