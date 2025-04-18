import secrets
from collections.abc import Sequence
from uuid import UUID

from fastapi import Depends

from src.application.middlewares.user_context import get_current_user_id
from src.domain.entity import Token
from src.persistence import TokenRepository


class TokenService:
    def __init__(self, repository: TokenRepository = Depends()):
        self.repository = repository

    async def get_all(self) -> Sequence[Token]:
        return await self.repository.get_all()

    async def get_by_id(self, token_id: UUID) -> Token | None:
        return await self.repository.get_by_id(token_id)

    async def get_by_filter_one(
        self,
        product_id: UUID | None = None,
        user_id: UUID | None = None,
    ):
        filter_by = {
            "product_id": product_id,
            "user_id": user_id,
        }
        return await self.repository.filter_by_one(filter_by)

    async def delete(self, token_id: UUID):
        await self.repository.delete(token_id)

    async def create(self, name: str) -> Token:
        name = name.strip()
        if name == "":
            raise
        data = {
            "token": secrets.token_hex(16),
            "creator_id": get_current_user_id(),
            "name": name,
        }
        return await self.repository.create(data)
