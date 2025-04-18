from collections.abc import Sequence
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity import Token
from src.infrastructure.database import get_session
from src.persistence.base import BaseRepository


class TokenRepository(BaseRepository[Token]):
    def __init__(self, session: Annotated[AsyncSession, Depends(get_session)]):
        super().__init__(Token, session)

    # TODO: Make it for generic use
    async def filter_by(self, filter_by: dict) -> Sequence[Token]:
        stmt = select(Token).filter_by(**filter_by)
        query = await self.session.execute(stmt)
        return query.scalars().all()

    async def filter_by_one(self, filter_by: dict) -> Token | None:
        filter_by_db = {k: v for k, v in filter_by.items() if v is not None}
        stmt = select(Token).filter_by(**filter_by_db)
        query = await self.session.execute(stmt)
        return query.scalars().first()
