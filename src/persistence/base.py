from collections.abc import Sequence
from math import ceil
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, NonNegativeInt, PositiveInt
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity.base import Base


class Pagination(BaseModel):
    total: NonNegativeInt
    size: NonNegativeInt
    page: NonNegativeInt
    total_page: NonNegativeInt
    data: Sequence


Entity = TypeVar("Entity", bound=Base)


class BaseRepository(Generic[Entity]):
    model: type[Entity]

    def __init__(self, model: type[Entity], session: AsyncSession):
        self.model = model
        self.session = session

    async def pagination(
        self,
        stmt: Select,
        page: PositiveInt = 1,
        scalars: bool = False,
    ):
        limit = 25
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

    async def get_all(self) -> Sequence[Entity]:
        stmt = select(self.model).order_by(self.model.created_at.desc())
        stmt = self._options(stmt)
        query = await self.session.execute(stmt)
        return query.scalars().all()

    async def get_all_by_filter(self, filters: dict) -> Sequence[Entity]:
        stmt = select(self.model).filter_by(**filters)
        query = await self.session.execute(stmt)
        return query.scalars().all()

    async def get_by_id(self, item_id: UUID) -> Entity | None:
        stmt = (
            select(self.model)
            .where(self.model.id == item_id)
            .order_by(self.model.created_at.desc())
        )
        stmt = self._options(stmt)
        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def get_one_by_id(self, item_id: UUID) -> Entity:
        stmt = (
            select(self.model)
            .where(self.model.id == item_id)
            .order_by(self.model.created_at.desc())
        )
        stmt = self._options(stmt)
        query = await self.session.execute(stmt)
        return query.scalar_one()

    async def get_by_filter(self, filters: dict) -> Entity | None:
        stmt = select(self.model).filter_by(**filters)
        query = await self.session.execute(stmt)
        return query.scalar_one_or_none()

    async def create(self, data: dict, *args, **kwargs) -> Entity:
        db = self.model(**data)
        self.session.add(db)
        await self.session.commit()
        await self.session.refresh(db)
        return db

    async def create_bulk(
        self, data_list: list[dict], commit: bool = True, *args, **kwargs
    ):
        db_list = []
        for data in data_list:
            db_list.append(self.model(**data))
        self.session.add_all(db_list)
        if commit:
            await self.session.commit()

    async def update(self, item_id: UUID, data: dict, *args, **kwargs) -> Entity:
        target = await self.get_by_id(item_id)
        if target is None:
            raise

        for k, v in data.items():
            setattr(target, k, v)

        await self.session.commit()
        await self.session.refresh(target)
        return target

    async def delete(self, item_id: UUID, target: Entity | None = None):
        if target is None:
            target = await self.get_by_id(item_id)
        await self.session.delete(target)
        await self.session.commit()

    def _options(self, stmt: Select) -> Select:
        return stmt
