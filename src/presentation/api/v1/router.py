from fastapi import APIRouter, Depends

from src.presentation.api.dependencies import SetContextUser
from src.presentation.api.v1.upload import router as Upload
from src.presentation.dependencies import PermissionChecker

router = APIRouter(
    prefix="", dependencies=[Depends(SetContextUser()), Depends(PermissionChecker())]
)
router.include_router(Upload)
