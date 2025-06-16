from datetime import datetime, timedelta
from uuid import UUID

import pytz
from fastapi import Depends

from src.application.schemas.finding import FindingActionInternalSchema
from src.domain.constant import FnStatusEnum, SeverityEnum
from src.domain.entity.finding import Finding, FindingName
from src.persistence import (
    FindingNameRepository,
    FindingRepository,
    FindingRevertRepository,
    GlobalRepository,
    PluginRepository,
)
from src.persistence.base import Pagination


class FindingService:
    def __init__(
        self,
        repository: FindingRepository = Depends(),
        findingname_repository: FindingNameRepository = Depends(),
        revert_repository: FindingRevertRepository = Depends(),
        global_repository: GlobalRepository = Depends(),
        plugin_repository: PluginRepository = Depends(),
    ):
        self.repository = repository
        self.findingname_repository = findingname_repository
        self.revert_repository = revert_repository
        self.global_repository = global_repository
        self.plugin_repository = plugin_repository

    async def get_by_product_id(self, product_id: UUID):
        return await self.repository.get_by_product_id_extended(product_id)

    async def get_group_by_severity_status(
        self,
        product_id: UUID | None = None,
        page: int = 1,
        filters: dict | None = None,
        include_sla: bool = True,
    ):
        if filters is None:
            filters = {}
        res = await self.repository.get_group_by_severity_status(
            product_id, filters, page
        )
        sources = await self.plugin_repository.get_all()
        source_dict = {str(s.id): s.name.title() for s in sources}
        data = {"findings": res, "sla": None, "source": source_dict}

        if include_sla:
            data["sla"] = await self._include_sla(res)
        return data

    async def get_group_by_asset_details(
        self, host: str, filters: dict | None = None, page: int = 1
    ):
        return await self.repository.get_group_by_asset_details(host, filters, page)

    async def get_group_by_assets(
        self, product_id: UUID | None = None, page: int = 1, filters: dict | None = None
    ):
        if filters is None:
            filters = {}
        res = await self.repository.get_group_by_asset(product_id, filters, page)
        return {"findings": res}

    async def get_breached_findings(
        self, product_id: UUID, severity: SeverityEnum = SeverityEnum.CRITICAL
    ):
        res = await self.repository.get_breached_findings_by_severity(
            product_id, severity
        )
        sla = await self.global_repository.get_sla_by_severity(severity)
        return {"findings": res, "sla": sla}

    async def _include_sla(self, res: Pagination):
        sla = await self.global_repository.get()
        sla_mapping = {}
        for finding in res.data:
            severity = finding[2]
            finding_date: datetime = finding[5]
            try:
                sla_val = getattr(sla, "sla_" + severity.value.lower())
            except:  #  noqa: E722
                sla_val = 10
            sla_mapping[finding[0]] = (
                finding_date + timedelta(sla_val) - datetime.now(pytz.utc)
            ).days
        return sla_mapping

    async def update(
        self, item_id: UUID, filters: dict, data: FindingActionInternalSchema
    ):
        await self.repository.update(item_id, filters, data.model_dump())

    async def bulk_update(self, filters: dict, data: dict):
        await self.repository.bulk_update(filters, data)

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

        plugin = await self.plugin_repository.get_by_filter({"name": "manual"})
        data["plugin_id"] = plugin.id if plugin else None

        return await self.repository.create(data)

    async def revert(self, product_id: UUID):
        can_revert = await self.can_revert(product_id)
        if can_revert:
            await self.revert_repository.revert(product_id)

    async def can_revert(self, product_id: UUID):
        curr = await self.repository.get_latest_date_by_product_id(product_id)
        prev = await self.revert_repository.get_latest_date_by_product_id(product_id)
        if prev is None or curr is None:
            return False
        return curr > prev

    async def delete_by_filter(self, product_id: UUID, filters: dict):
        return await self.repository.delete_by_filter(product_id, filters)
