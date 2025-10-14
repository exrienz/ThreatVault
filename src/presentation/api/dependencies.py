from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.middlewares.user_context import (
    current_user_id_var,
    current_user_var,
)
from src.domain.constant import ApiKeyTypeEnum
from src.domain.entity.project_management import Product
from src.domain.entity.token import Token
from src.domain.entity.user_access import Role, User
from src.infrastructure.database.session import get_session


class SetContextUser:
    async def __call__(
        self,
        session: Annotated[AsyncSession, Depends(get_session)],
        Authorization: Annotated[str | None, Header()] = None,
    ):
        if Authorization is None:
            return
        token_type, product_id, project_id = await self.get_api_user_info(
            session, Authorization
        )
        if token_type is None:
            return
        data = await self.set_user_info(session, token_type, product_id, project_id)

        current_user_id_var.set(data.get("userid"))
        current_user_var.set(data)

    async def get_api_user_info(self, session: AsyncSession, token: str):
        glb_stmt = select(Token).where(Token.token == token)
        query = await session.execute(glb_stmt)
        glb_token = query.scalar_one_or_none()
        if glb_token:
            return ApiKeyTypeEnum.Global, None, None
        pr_stmt = (
            select(Product)
            .options(selectinload(Product.environment))
            .where(Product.apiKey == token)
        )
        query = await session.execute(pr_stmt)
        pr_token = query.scalar_one_or_none()
        if pr_token:
            return ApiKeyTypeEnum.Product, pr_token.id, pr_token.environment.project_id
        return None, None, None

    async def set_user_info(
        self,
        session: AsyncSession,
        token_type: ApiKeyTypeEnum,
        product_id: UUID | None = None,
        project_id: UUID | None = None,
    ):
        acc_stmt = (
            select(User)
            .join(Role)
            .options(selectinload(User.role))
            .where(Role.name == "Service")
            .order_by(User.created_at)
        )
        acc_query = await session.execute(acc_stmt)
        user = acc_query.scalars().first()
        if user is None:
            raise
        return {
            "userid": str(user.id),
            "role": user.role.name,
            "is_admin": False,
            "high_privilege": True,
            "role_id": str(user.role_id),
            "required_project_access": token_type == ApiKeyTypeEnum.Global,
            "token_type": token_type.value,
            "service_product_id": product_id,
            "service_project_id": project_id,
            "username": user.username,
            "exp": (datetime.now() + timedelta(days=30)).timestamp(),
        }
