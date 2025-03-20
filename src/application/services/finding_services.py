from uuid import UUID

from fastapi import Depends

from src.persistence import FindingNameRepository, FindingRepository


class FindingService:
    def __init__(
        self,
        repository: FindingRepository = Depends(),
        findingname_repository: FindingNameRepository = Depends(),
    ):
        self.repository = repository
        self.findingname_repository = findingname_repository

    async def get_by_product_id(self, product_id: UUID):
        return await self.repository.get_by_product_id_extended(product_id)

    async def get_group_by_severity_status(self, product_id: UUID, page: int = 1):
        return await self.repository.get_group_by_severity_status(product_id, page)

    async def update(self, item_id: UUID, host_list: list, data: dict):
        await self.repository.update(item_id, host_list, data)

    async def get_by_id_extended(self, item_id: UUID):
        return await self.findingname_repository.get_by_filter(item_id)
