from datetime import datetime
from uuid import UUID

from fastapi import Depends

from src.domain.constant import FnStatusEnum
from src.domain.entity.finding import Finding, FindingName, FindingRevertPoint
from src.persistence import (
    FindingNameRepository,
    FindingRepository,
    FindingRevertRepository,
)


class FindingService:
    def __init__(
        self,
        repository: FindingRepository = Depends(),
        findingname_repository: FindingNameRepository = Depends(),
        revert_repository: FindingRevertRepository = Depends(),
    ):
        self.repository = repository
        self.findingname_repository = findingname_repository
        self.revert_repository = revert_repository

    async def get_by_product_id(self, product_id: UUID):
        return await self.repository.get_by_product_id_extended(product_id)

    async def get_group_by_severity_status(self, product_id: UUID, page: int = 1):
        return await self.repository.get_group_by_severity_status(product_id, page)

    async def update(self, item_id: UUID, host_list: list, data: dict):
        await self.repository.update(item_id, data, host_list)

    async def get_by_id_extended(self, item_id: UUID) -> FindingName:
        finding_name = await self.findingname_repository.get_by_filter(
            {"finding_name_id": item_id}
        )
        if finding_name is None:
            raise
        return finding_name

    async def manual_upload(self, fn_data: dict, data: dict) -> Finding:
        finding_name = await self.findingname_repository.get_by_filter(fn_data)

        if finding_name is None:
            finding_name = await self.findingname_repository.create(fn_data)
        data["finding_name_id"] = finding_name.id
        data["status"] = FnStatusEnum.NEW
        data["last_update"] = data.get("finding_date", datetime.now())

        return await self.repository.create(data)

    async def revert(self, product_id: UUID):
        await self.revert_repository.revert(product_id)

    async def can_revert(self, product_id: UUID):
        curr = await self.repository.get_latest_date_by_product_id(product_id)
        prev = await self.revert_repository.get_latest_date_by_product_id(product_id)
        if prev is None or curr is None:
            return False
        return curr > prev
