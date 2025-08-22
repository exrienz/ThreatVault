from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy import Select, select
from sqlalchemy import delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entity import (
    Environment,
    Finding,
    Product,
    ProductUserAccess,
    User,
)
from src.domain.entity.user_access import Role
from src.infrastructure.database import get_session
from src.persistence.base import BaseRepository
from src.presentation.dependencies import get_allowed_product_ids


class ProductRepository(BaseRepository[Product]):
    def __init__(
        self,
        session: Annotated[AsyncSession, Depends(get_session)],
        product_ids: Annotated[list[UUID] | None, Depends(get_allowed_product_ids)],
    ):
        super().__init__(Product, session, product_ids=product_ids)

    def _options(self, stmt: Select):
        return stmt.options(
            selectinload(Product.environment).selectinload(Environment.project),
        )

    async def get_by_id_filter(
        self,
        project_id: UUID | None = None,
        environment_id: UUID | None = None,
    ) -> Sequence[Product]:
        stmt = select(Product).join(Environment)
        if project_id:
            stmt = stmt.where(Environment.project_id == project_id)
        if environment_id:
            stmt = stmt.where(Environment.id == environment_id)
        query = await self.session.execute(stmt)
        return query.scalars().all()

    async def product_access(
        self,
        product_id: UUID,
        user_id: UUID,
    ) -> ProductUserAccess | None:
        stmt = (
            select(ProductUserAccess)
            .where(
                ProductUserAccess.product_id == product_id,
                ProductUserAccess.user_id == user_id,
            )
            .options(selectinload(ProductUserAccess.user))
        )

        query = await self.session.execute(stmt)
        return query.scalar()

    async def product_access_list(
        self, role_id: UUID | None = None, user_id: UUID | None = None
    ) -> Sequence[Product]:
        stmt = (
            (select(Product).join(ProductUserAccess).join(User))
            .options(
                selectinload(Product.accesses).joinedload(ProductUserAccess.user),
                selectinload(Product.environment),
            )
            .where(User.active.is_(True))
        )
        if role_id:
            stmt = stmt.where(User.role_id == role_id)
        if user_id:
            stmt = stmt.where(User.id == user_id)
        query = await self.session.execute(stmt)
        return query.scalars().all()

    async def create_product_access(
        self, product_id: UUID, user_id: UUID, granted: bool = True
    ) -> ProductUserAccess:
        db_data = ProductUserAccess(
            product_id=product_id, user_id=user_id, granted=granted
        )
        self.session.add(db_data)
        await self.session.commit()
        await self.session.refresh(db_data)
        permission = await self.product_access(product_id, user_id)
        if permission is None:
            raise
        return permission

    async def manage_product_access(
        self, product_id, user_id: UUID, granted: bool = True
    ) -> ProductUserAccess | None:
        permission = await self.product_access(product_id, user_id)
        if granted:
            if permission:
                return permission
            return await self.create_product_access(product_id, user_id, granted)
        if permission:
            return await self.delete_product_access(permission)
        return None

    async def delete_product_access(self, permission: ProductUserAccess):
        await self.session.delete(permission)

    async def get_hosts(self, product_id: UUID) -> Sequence[str]:
        stmt = select(Finding.host).where(Finding.product_id == product_id).distinct()
        query = await self.session.execute(stmt)
        return query.scalars().all()

    def _product_allowed_ids(self, stmt: Select) -> Select:
        if self.allowed_product_ids is None:
            return stmt
        return stmt.where(Product.id.in_(self.allowed_product_ids))

    async def get_owners_by_product_id(self, product_id: UUID) -> Sequence[User]:
        stmt = (
            select(User)
            .join(ProductUserAccess)
            .join(Role)
            .where(
                ProductUserAccess.product_id == product_id,
                ProductUserAccess.granted.is_(True),
                Role.name == "Owner",
            )
        )

        query = await self.session.execute(stmt)
        return query.scalars().all()

    async def delete(self, item_id: UUID, target: Product | None = None):
        sub = (
            select(Finding.id).where(Finding.product_id == item_id)
        ).scalar_subquery()
        stmt = sql_delete(Finding).where(Finding.id.in_(sub))
        await self.session.execute(stmt)
        await super().delete(item_id, target)

    async def delete_by_project_id(self, project_id: UUID):
        sub = (
            select(Product.id)
            .join(Environment, Environment.id == Product.environment_id)
            .where(Environment.project_id == project_id)
        ).scalar_subquery()

        fn_delete_stmt = sql_delete(Finding).where(Finding.product_id.in_(sub))
        delete_stmt = sql_delete(Product).where(Product.id.in_(sub))
        await self.session.execute(fn_delete_stmt)
        await self.session.execute(delete_stmt)
        await self.session.commit()
