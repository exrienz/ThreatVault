from collections.abc import Sequence
from math import ceil
from types import MethodType
from typing import Generic, TypeVar, Union
from uuid import UUID

from pydantic import BaseModel, NonNegativeInt, PositiveInt
from sqlalchemy import Delete, Select, Update, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from src.application.middlewares.user_context import get_current_user
from src.domain.entity.base import Base

AdvFilterType = dict[Union[MethodType, InstrumentedAttribute], object]


class Pagination(BaseModel):
    total: NonNegativeInt
    size: NonNegativeInt
    page: NonNegativeInt
    total_page: NonNegativeInt
    data: Sequence


Entity = TypeVar("Entity", bound=Base)


class BaseRepository(Generic[Entity]):
    model: type[Entity]

    def __init__(
        self,
        model: type[Entity],
        session: AsyncSession,
        project_ids: list[UUID] | None = None,
        product_ids: list[UUID] | None = None,
    ):
        self.model = model
        self.session = session
        self.current_user = get_current_user()
        self.allowed_project_ids = project_ids
        self.allowed_product_ids = product_ids

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

        if stmt._group_by_clauses:
            total_query = select(func.count().label("total")).select_from(stmt.alias())
        else:
            total_query = stmt.with_only_columns(func.count().label("total"))

        query = await self.session.execute(total_query.order_by(None))
        total = query.scalar() or 0

        return Pagination(
            total=total,
            size=limit,
            page=page,
            total_page=ceil(total / limit),
            data=findings,
        )

    def _orders(self, stmt) -> Select:
        return stmt.order_by(self.model.created_at.desc())

    async def get_all(self) -> Sequence[Entity]:
        stmt = select(self.model)
        stmt = self._options(stmt)
        stmt = self._orders(stmt)
        stmt = self._permission_filter(stmt)
        query = await self.session.execute(stmt)
        return query.scalars().all()

    # TODO: Deprecated
    async def get_all_by_filter(
        self,
        filters: dict,
        order_by: list | None = None,
        pagination: bool = False,
        page: int = 1,
    ) -> Sequence[Entity] | Pagination:
        if pagination:
            return await self.get_all_by_filter_pagination(filters, order_by, page)
        return await self.get_all_by_filter_sequence(filters, order_by)

    def _get_all(self, filters: dict, order_by: list | None = None) -> Select:
        order_cols = ["created_at"]
        if order_by:
            order_cols = [getattr(self.model, col) for col in order_by]
        stmt = self._get(filters).order_by(*order_cols)
        stmt = self._permission_filter(stmt)
        return stmt

    async def get_all_by_filter_sequence(
        self,
        filters: dict,
        order_by: list | None = None,
    ) -> Sequence[Entity]:
        stmt = self._get_all(filters, order_by)
        query = await self.session.execute(stmt)
        return query.unique().scalars().all()

    async def get_all_by_filter_pagination(
        self,
        filters: dict,
        order_by: list | None = None,
        page: int = 1,
    ) -> Pagination:
        stmt = self._get_all(filters, order_by)
        return await self.pagination(stmt, page, scalars=True)

    async def get_by_id(self, item_id: UUID) -> Entity | None:
        stmt = select(self.model).where(self.model.id == item_id)
        stmt = self._orders(stmt)
        stmt = self._options(stmt)
        stmt = self._permission_filter(stmt)
        query = await self.session.execute(stmt)
        return query.scalars().first()

    async def get_one_by_id(self, item_id: UUID) -> Entity:
        stmt = select(self.model).where(self.model.id == item_id)
        stmt = self._options(stmt)
        stmt = self._permission_filter(stmt)
        query = await self.session.execute(stmt)
        return query.scalar_one()

    async def get_by_filter(self, filters: dict) -> Entity | None:
        stmt = self._get(filters)
        query = await self.session.execute(stmt)
        return query.unique().scalar_one_or_none()

    async def get_first_by_filter(self, filters: dict, order_by: list) -> Entity | None:
        order_cols = [getattr(self.model, col) for col in order_by]
        stmt = self._get(filters).order_by(*order_cols)
        query = await self.session.execute(stmt)
        return query.scalars().first()

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

    async def update(self, item_id: UUID, data: dict, *args, **kwargs) -> Entity | None:
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

    def _permission_filter(self, stmt: Select) -> Select:
        stmt = self._project_allowed_ids(stmt)
        return self._product_allowed_ids(stmt)

    def _project_allowed_ids(self, stmt: Select) -> Select:
        return stmt

    def _product_allowed_ids(self, stmt: Select) -> Select:
        return stmt

    def _get(self, filters: dict) -> Select:
        stmt = select(self.model)
        if filters:
            key = next(iter(filters))
            if isinstance(key, (MethodType, InstrumentedAttribute)):
                stmt = self._advanced_filtering(stmt, filters)
            else:
                stmt = self._filters(stmt, filters)
        stmt = self._options(stmt)
        stmt = self._permission_filter(stmt)
        return stmt

    def _filters(self, stmt: Select | Update | Delete, filters: dict):
        # stmt = select(self.model)
        filters_ = {}
        for k, v in filters.items():
            if isinstance(v, list):
                stmt = stmt.where(getattr(self.model, k).in_(v))
            else:
                filters_[k] = v

        stmt = stmt.filter_by(**filters_)
        return stmt

    def _advanced_filtering(self, stmt: Select, filters: AdvFilterType):
        for k, v in filters.items():
            if v is None:
                continue
            if isinstance(k, InstrumentedAttribute):
                stmt = stmt.where(k == v)
            elif isinstance(k, MethodType):
                stmt = stmt.where(k(v))
        return stmt
