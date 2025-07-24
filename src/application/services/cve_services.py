from fastapi import Depends

from src.infrastructure.database.config import AsyncSessionFactory
from src.infrastructure.services.priority import PriorityCalculator
from src.persistence import CVERepository


class CVEService:
    def __init__(
        self,
        repository: CVERepository = Depends(),
    ):
        self.repository = repository

    async def calculate_priority(self, recalculate: bool = True):
        if recalculate:
            data = await self.repository.get_all()
        else:
            data = await self.repository.get_cves_without_priority()
        cve_list = [d.name for d in data if d.name]
        cve_ids = {d.name: d.id for d in data}
        result = await PriorityCalculator(cve_list).process()

        priority_data = []
        for res in result:
            cve_id = res.pop("cve_id")
            if cve_id is None:
                continue
            new_data = {"id": cve_ids.get(cve_id), **res}
            priority_data.append(new_data)
        await self.repository.update_bulk(priority_data)

    @classmethod
    async def create(cls):
        async with AsyncSessionFactory() as session:
            repository = CVERepository(session)
            return CVEService(repository)
