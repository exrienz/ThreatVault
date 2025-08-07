from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from fastapi import Depends

from src.application.schemas import YearlyStatisticFilterSchema
from src.application.schemas.chart import YearlyProductStatisticsSchema
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

    def _total_products_stats(self, data: Sequence, labels: list[str]) -> list[int]:
        total = [0] * len(labels)
        for d in data:
            for i in range(len(labels)):
                total[i] += getattr(d, f"t{labels[i].title()}")
        return total

    async def get_products_by_env(
        self,
        filters: YearlyStatisticFilterSchema,
    ):
        if filters.date_str:
            filters.year, filters.month = filters.date_str.year, filters.date_str.month
        else:
            today = datetime.now()
            if filters.year is None:
                filters.year = today.year
            if filters.month is None:
                filters.month = today.month
        if filters.env_id is None:
            raise

        data = await self.repository.get_products_by_env(
            filters.env_id, filters.year, filters.month
        )

        data_dct = {row.product_id: row for row in data}
        labels = await self.repository._get_statistics_labels(
            filters.view_type, env_id=filters.env_id
        )
        total = self._total_products_stats(data, labels)

        # others included in closed
        if labels[-1] == "Others":
            others = total.pop()
            total[2] += others

        return {
            "data": data_dct,
            "year": filters.year,
            "month": filters.month,
            "total": total,
            "labels": labels,
        }

    async def get_products_by_env_view(
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

    def _yearly_dict_process(
        self, chart_data: Sequence, labels: list[str], prefix: str = ""
    ) -> dict:
        if not labels:
            raise
        dct = {label: [0] * 12 for label in labels}
        for c in chart_data:
            mnt = int(c.month) - 1
            for label in labels:
                dct[label][mnt] = getattr(c, f"{prefix}{label}")
        return dct

    async def get_yearly_statistics(self, filters: YearlyStatisticFilterSchema):
        if filters.year is None:
            today = datetime.now()
            filters.year = today.year

        chart_data = await self.repository.statistics_by_environment(
            filters.project_id,
            filters.env_id,
            filters.year,
            filters.month,
            filters.view_type,
        )

        labels = await self.repository._get_statistics_labels(
            filters.view_type, filters.project_id, filters.env_id
        )
        chart = self._yearly_dict_process(chart_data, labels)
        chart_lst = []
        labels = []
        for k, v in chart.items():
            labels.append(k)
            chart_lst.append({"name": k, "data": v})
        return (
            chart_lst,
            filters.year,
            filters.month,
            labels,
        )

    async def get_product_yearly_statistics(
        self, filters: YearlyProductStatisticsSchema
    ):
        if filters.year is None:
            today = datetime.now()
            filters.year = today.year

        chart_data = await self.repository.get_yearly_log_by_product_ids(
            [filters.product_id], filters.year
        )

        labels = await self.repository._get_statistics_labels(
            filters.view_type, product_id=filters.product_id
        )
        chart = self._yearly_dict_process(chart_data, labels, "t")
        chart_lst = []
        labels = []
        for k, v in chart.items():
            labels.append(k)
            chart_lst.append({"name": k, "data": v})
        return (
            chart_lst,
            filters.year,
            labels,
        )

    # Deprecated
    async def get_statistic_by_env_filters(
        self,
        env_id: UUID,
        year: int | None = None,
        month: int | None = None,
        type_: str = "severity",
    ):
        today = datetime.now()
        if year is None:
            year = today.year

        chart_data = await self.repository.statistics_by_environment(
            env_id, year, month, type_
        )

        type_map = {
            "severity": ["Critical", "High", "Medium", "Low"],
            "status": ["New", "Open", "Closed", "Exemption", "Others"],
            "status_va": ["New", "Open", "Closed", "Exemption", "Others"],
            "status_ha": ["Passed", "Warning", "Failed"],
        }
        labels = type_map.get(type_, [])
        return (
            self._yearly_dict_process(chart_data, labels),
            year,
            month,
        )

    async def get_logs_yearly(self, product_ids: list[UUID], year: int | None):
        return await self.repository.get_yearly_log_by_product_ids(product_ids, year)

    async def get_logs_yearly_env(
        self, env_id: UUID, year: int | None, severity: str | None = None
    ):
        data = await self.repository.get_yearly_log_by_env_id(env_id, year)
        severity_sets = {"Critical", "High", "Medium", "Low"}
        chart_dct: dict[str, list] = {}
        for d in data:
            if chart_dct.get(d.product_name) is None:
                chart_dct[d.product_name] = [None] * 12
            severity = str(severity).title()
            if severity not in severity_sets:
                add_data = sum([getattr(d, f"b{x}") for x in severity_sets])
            else:
                add_data = getattr(d, f"b{severity}")
            chart_dct[d.product_name][int(d.month) - 1] = add_data
        return [{"name": k, "data": v} for k, v in chart_dct.items()]
