from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from src.domain.entity.finding import AdditionalRemark
from src.persistence import AdditionalRemarkRepository


class RemarkService:
    def __init__(self, repository: Annotated[AdditionalRemarkRepository, Depends()]):
        self.repository = repository

    async def get_by_filters(self, filters: dict):
        return await self.repository.get_by_filter(filters)

    async def create(self, data: dict):
        return await self.repository.create(data)

    async def update(self, remark_id: UUID, data: dict):
        return await self.repository.update(remark_id, data)

    async def get_all_by_product_ids(
        self, product_ids: list[UUID], filters: dict | None = None
    ) -> Sequence[AdditionalRemark]:
        if filters is None:
            filters = {}
        filters["product_id"] = product_ids
        return await self.repository.get_all_by_filter_sequence(filters)
