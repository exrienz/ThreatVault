from collections.abc import Sequence

from fastapi import Depends

from src.domain.entity import Role
from src.persistence import RoleRepository


class RoleService:
    def __init__(self, repository: RoleRepository = Depends()):
        self.repository = repository

    async def get_all(self) -> Sequence[Role]:
        return await self.repository.get_all()
