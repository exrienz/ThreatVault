from fastapi import Depends

from src.domain.entity import GlobalConfig
from src.persistence import GlobalRepository


class GlobalService:
    def __init__(self, repository: GlobalRepository = Depends()):
        self.repository = repository

    async def get(self) -> GlobalConfig | None:
        return await self.repository.get()

    async def update(self, data: dict) -> GlobalConfig:
        config = await self.repository.get()
        if config is None:
            return await self.repository.create(data)
        return await self.repository.update(config.id, data)
