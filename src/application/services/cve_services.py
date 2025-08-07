from collections.abc import Sequence

from fastapi import Depends

from src.domain.entity.finding import CVE
from src.infrastructure.database.config import AsyncSessionFactory
from src.infrastructure.services.priority import PriorityCalculator
from src.persistence import CVERepository


class CVEService:
    def __init__(
        self,
        repository: CVERepository = Depends(),
    ):
        self.repository = repository

    async def update_bulk(self, data: list):
        return await self.repository.update_bulk(data)

    async def get_cves(self, get_all: bool = True) -> Sequence[CVE]:
        if get_all:
            return await self.repository.get_all()
        else:
            return await self.repository.get_cves_without_priority()

    @classmethod
    async def generate_priority(cls):
        data = []
        async with AsyncSessionFactory() as session:
            repository = CVERepository(session)
            data = await CVEService(repository).get_cves()

        cve_list = [d.name for d in data if d.name]
        cve_ids = {d.name: d.id for d in data}
        chunksize = 10

        for i in range(0, len(cve_list), chunksize):
            await cls.search_and_upload(cve_list[i : i + chunksize], cve_ids)

    @classmethod
    async def bulk_update(cls, priority_data: list):
        async with AsyncSessionFactory() as session:
            repository = CVERepository(session)
            await CVEService(repository).update_bulk(priority_data)

    @classmethod
    async def search_and_upload(cls, cve_list: list, cve_ids: dict):
        result = await PriorityCalculator(cve_list).process()
        priority_data = []
        for res in result:
            cve_id = res.pop("cve_id")
            if cve_id is None:
                continue
            new_data = {"id": cve_ids.get(cve_id), **res}
            priority_data.append(new_data)
        if len(priority_data) > 0:
            await cls.bulk_update(priority_data)
