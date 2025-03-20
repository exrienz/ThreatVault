from collections.abc import Sequence
from uuid import UUID

from fastapi import Depends

from src.domain.entity import Environment
from src.persistence import EnvRepository


class EnvService:
    def __init__(self, repository: EnvRepository = Depends()) -> None:
        self.repository = repository

    async def get_by_project_id(self, project_id: UUID) -> Sequence[Environment]:
        res = await self.repository.get_all_by_filter(project_id=project_id)
        if res is None:
            raise
        return res

    async def get_by_filter(self, project_id: UUID, name: str) -> Environment:
        res = await self.repository.get_by_filter(name, project_id)
        if res is None:
            raise
        return res
