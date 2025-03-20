from uuid import UUID, uuid4

from fastapi import Depends
from pydantic import PositiveInt

from src.persistence.user import UserRepository


class UserService:
    def __init__(self, repository: UserRepository = Depends()):
        self.repository = repository

    async def get_current_user_id(self) -> UUID:
        return uuid4()

    async def get_all(self, page: PositiveInt = 1, filters: dict | None = None):
        return await self.repository.get_all(page, filters)
