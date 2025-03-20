from fastapi import APIRouter

from .finding import router as Finding
from .manage_user import router as User
from .product import router as Product
from .project_management import router as PM

v1_router = APIRouter(prefix="")
v1_router.include_router(PM)
v1_router.include_router(Product)
v1_router.include_router(Finding)
v1_router.include_router(User)
