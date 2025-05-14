from collections.abc import Sequence
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from pydantic import PositiveInt
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entity import Environment, Product, ProductUserAccess, Role, User
from src.infrastructure.database import get_session
from src.persistence.base import BaseRepository, Pagination


class UserRepository(BaseRepository[User]):
    def __init__(self, session: Annotated[AsyncSession, Depends(get_session)]):
        super().__init__(User, session)

    # TODO: Generalize get_all_by_filters
    async def get_all_pagination(
        self,
        page: PositiveInt = 1,
        filters: dict | None = None,
        pagination: bool = True,
    ) -> Pagination | Sequence[User]:
        stmt = select(User).join(Role).options(selectinload(User.role))
        if filters:
            if (val := filters.get("email")) is not None:
                stmt = stmt.where(User.email.ilike(f"%{val}%"))
            if (val := filters.get("role")) is not None:
                stmt = stmt.where(Role.name.ilike(f"%{val}%"))
            if (val := filters.get("active")) is not None:
                stmt = stmt.where(User.active.is_(val))
            if (val := filters.get("role_id")) is not None:
                stmt = stmt.where(User.role_id == val)
        if pagination:
            return await self.pagination(stmt, page, True)
        query = await self.session.execute(stmt)
        return query.scalars().all()

    def _options(self, stmt: Select):
        return stmt.options(selectinload(User.role))

    async def get_accessible_product(self, user_id: UUID):
        stmt = (
            select(Product)
            .join(ProductUserAccess)
            .where(ProductUserAccess.user_id == user_id)
        ).options(selectinload(Product.environment).joinedload(Environment.project))

        query = await self.session.execute(stmt)
        return query.scalars().all()

    async def get_users_with_product_accesibility(
        self,
        product_id: UUID,
        allowed: bool = True,
        exclude_roles: list | None = None,
    ):
        stmt = (
            select(User)
            .join(Role)
            .options(selectinload(User.role))
            .where(Role.required_project_access.is_(True), User.active.is_(True))
        )
        inner_stmt = select(ProductUserAccess.user_id).where(
            ProductUserAccess.product_id == product_id,
            ProductUserAccess.granted.is_(True),
        )

        if allowed:
            stmt = stmt.where(User.id.in_(inner_stmt))
        else:
            stmt = stmt.where(User.id.notin_(inner_stmt))

        if exclude_roles:
            stmt = stmt.where(Role.name.not_in(exclude_roles))
        query = await self.session.execute(stmt)
        return query.scalars().all()

    async def delete(self, item_id: UUID, target: User | None = None):
        if target is None:
            target = await self.get_one_by_id(item_id)
        target.deleted_at = datetime.now()
        await self.session.commit()
