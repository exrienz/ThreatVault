from datetime import datetime
from uuid import UUID

from fastapi import Depends

from src.domain.entity import Log
from src.persistence import LogRepository


class LogService:
    def __init__(self, repository: LogRepository = Depends()):
        self.repository = repository

    async def get_by_product_id(self, product_id: UUID) -> Log | None:
        return await self.repository.get_by_product_id(product_id)

    async def calculate(self, product_id: UUID, scan_date: datetime):
        return await self.repository.calculate(product_id, scan_date)

    async def statistic(self, product_id: UUID, year: int):
        return await self.repository.statistics(product_id, year)
