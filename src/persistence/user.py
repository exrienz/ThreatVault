from math import ceil
from uuid import UUID, uuid4

from fastapi import Depends
from pydantic import PositiveInt
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entity import Role, User
from src.infrastructure.database.session import get_session
from src.persistence.finding import Pagination


class UserRepository:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session

    async def get_current_user_id(self) -> UUID:
        return uuid4()

    async def pagination(
        self,
        stmt: Select,
        page: PositiveInt = 1,
        scalars: bool = False,
    ):
        limit = 2
        fn_stmt = stmt.limit(limit).offset((page - 1) * limit)
        query = await self.session.execute(fn_stmt)
        if scalars:
            findings = query.scalars().all()
        else:
            findings = query.all()
        addition_query = stmt.with_only_columns(func.count().label("total"))
        query = await self.session.execute(addition_query)
        total = query.scalar() or 0

        return Pagination(
            total=total,
            size=limit,
            page=page,
            total_page=ceil(total / limit),
            data=findings,
        )

    async def get_all(
        self, page: PositiveInt = 1, filters: dict | None = None
    ) -> Pagination:
        stmt = select(User).join(Role).options(selectinload(User.role))
        if filters:
            if val := filters.get("email") is not None:
                stmt = stmt.where(User.email.ilike(val))
            if val := filters.get("role") is not None:
                stmt = stmt.where(Role.name.ilike(val))
            if val := filters.get("active") is not None:
                stmt = stmt.where(User.active.is_(val))
        return await self.pagination(stmt, page, True)
