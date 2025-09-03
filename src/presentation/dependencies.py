from datetime import datetime
from typing import Annotated

import pytz
from fastapi import Depends, HTTPException, status
from sqlalchemy import select

from src.application.middlewares.user_context import (
    current_user_perm,
    get_current_user,
)
from src.domain.entity.project_management import Environment, Product
from src.domain.entity.user_access import (
    Permission,
    ProductUserAccess,
    RolePermission,
)
from src.infrastructure.database.config import AsyncSessionFactory


async def verify_auth():
    user = get_current_user()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You need to log in",
            headers={"WWW-Authenticate": "Bearer"},
        )
    _expiration_handler(user)
    return user


def _expiration_handler(user_info: dict):
    expiration_seconds = user_info.get("exp")
    if expiration_seconds is None:
        raise

    dt = datetime.fromtimestamp(float(expiration_seconds), tz=pytz.utc)
    now = datetime.now(pytz.utc)

    if now > dt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expired Session",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_allowed_product_ids(user: Annotated[dict, Depends(verify_auth)]):
    if not user.get("required_project_access", True):
        return None
    async with AsyncSessionFactory() as session:
        stmt = (
            select(Product.id)
            .join(ProductUserAccess)
            .where(ProductUserAccess.user_id == user.get("userid"))
        )
        query = await session.execute(stmt)
        return query.scalars().all()


async def get_allowed_project_ids(user: Annotated[dict, Depends(verify_auth)]):
    if not user.get("required_project_access", True):
        return None
    async with AsyncSessionFactory() as session:
        stmt = (
            select(Environment.project_id)
            .select_from(ProductUserAccess)
            .join(Product, Product.id == ProductUserAccess.product_id)
            .join(Environment, Environment.id == Product.environment_id)
            .where(ProductUserAccess.user_id == user.get("userid"))
        )
        query = await session.execute(stmt)
        return query.scalars().all()


class PermissionChecker:
    def __init__(self, scopes: list[str] | None = None, admin_only: bool = False):
        if scopes is None:
            scopes = []
        self.scopes = set(scopes)
        self.admin_only = admin_only

    async def __call__(self, user: Annotated[dict, Depends(verify_auth)]):
        is_admin = user.get("is_admin", False)
        if self.admin_only:
            if is_admin:
                return
        else:
            if is_admin or user.get("high_privilege", False):
                current_user_perm.set(set(["all"]))
                return set(["all"])
            permissions = await self._get_permission(user)
            missing_perm = self.scopes - permissions
            if len(missing_perm) == 0:
                current_user_perm.set(permissions)
                return permissions
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this resource",
            headers={"WWW-Authenticate": f"Bearer scope={' '.join(self.scopes)}"},
        )

    async def _get_permission(self, user: dict) -> set:
        stmt = (
            select(Permission.scope)
            .join(RolePermission)
            .where(
                RolePermission.role_id == user.get("role_id"),
            )
        )
        async with AsyncSessionFactory() as session:
            query = await session.execute(stmt)
            res = query.scalars().all()
        return set(res)
