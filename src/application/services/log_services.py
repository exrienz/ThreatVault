from datetime import datetime
from uuid import UUID

from fastapi import Depends

from src.domain.entity import Log
from src.persistence import LogRepository, ProjectRepository

from ..middlewares.user_context import get_current_user_id


class LogService:
    def __init__(
        self,
        repository: LogRepository = Depends(),
        projectRepository: ProjectRepository = Depends(),
    ):
        self.repository = repository
        self.projectRepository = projectRepository
        self.user_id = get_current_user_id()

    async def get_by_product_id(self, product_id: UUID) -> Log | None:
        return await self.repository.get_by_product_id(product_id)

    async def get_prev_by_product_id(self, product_id: UUID) -> Log | None:
        return await self.repository.get_prev_by_product_id(product_id)

    async def get_products_by_env(
        self, env_id: UUID, year: int | None = None, month: int | None = None
    ):
        today = datetime.now()
        if year is None:
            year = today.year
        if month is None:
            month = today.month

        return (
            await self.repository.get_products_by_env(env_id, year, month),
            year,
            month,
        )

    async def get_available_date_by_env(self, env_id: UUID):
        return await self.repository.get_date_options_by_env(env_id)

    async def calculate(self, product_id: UUID, scan_date: datetime):
        if self.user_id is None:
            raise
        return await self.repository.calculate(product_id, self.user_id, scan_date)

    async def statistic(self, product_id: UUID, year: int):
        return await self.repository.statistics(product_id, year)

    async def get_statistic_by_env(
        self, env_id: UUID, year: int | None = None, month: int | None = None
    ):
        today = datetime.now()
        if year is None:
            year = today.year

        chart_data = await self.repository.statistics_by_environment(
            env_id, year, month
        )
        dct = {
            "Critical": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "High": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "Medium": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "Low": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        }
        for c in chart_data:
            mnt = int(c.month) - 1
            dct["Critical"][mnt] = c.tCritical
            dct["High"][mnt] = c.tHigh
            dct["Medium"][mnt] = c.tMedium
            dct["Low"][mnt] = c.tLow
        return dct, year, month
