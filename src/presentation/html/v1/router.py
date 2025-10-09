from fastapi import APIRouter, Depends

from src.presentation.dependencies import PermissionChecker
from src.presentation.html.dependencies import SetContextUser

from .auth import router as Auth
from .chart import router as Chart
from .cve import router as CVE
from .dashboard import router as Dashboard
from .finding import router as Finding
from .host import router as Host
from .llm_openai import router as OpenAI
from .manage_api import router as APIManager
from .manage_owner import router as OwnerManagement
from .manage_role import router as RoleManagement
from .manage_user import router as User
from .management_view import router as MV
from .plugin_management import router as Plugin
from .product import router as Product
from .project_management import router as PM
from .self_service import router as SelfService
from .setting import router as Setting

v1_router_with_auth = APIRouter(
    prefix="", dependencies=[Depends(SetContextUser()), Depends(PermissionChecker())]
)

v1_router_with_auth.include_router(Dashboard)
v1_router_with_auth.include_router(PM)
v1_router_with_auth.include_router(Product)
v1_router_with_auth.include_router(Finding)
v1_router_with_auth.include_router(User)
v1_router_with_auth.include_router(OwnerManagement)
v1_router_with_auth.include_router(Plugin)
v1_router_with_auth.include_router(Setting)
v1_router_with_auth.include_router(SelfService)
v1_router_with_auth.include_router(APIManager)
v1_router_with_auth.include_router(Host)
v1_router_with_auth.include_router(MV)
v1_router_with_auth.include_router(Chart)
v1_router_with_auth.include_router(CVE)
v1_router_with_auth.include_router(OpenAI)
v1_router_with_auth.include_router(RoleManagement)

v1_router = APIRouter(prefix="")
v1_router.include_router(Auth)
v1_router.include_router(v1_router_with_auth)
