from fastapi import Depends

from src.persistence import GlobalRepository


class GlobalService:
    def __init__(self, repository: GlobalRepository = Depends()):
        self.repository = repository

    async def get(self):
        return await self.repository.get()
