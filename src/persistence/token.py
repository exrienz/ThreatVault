from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entity import Token
from src.infrastructure.database import get_session
from src.persistence.base import BaseRepository


class TokenRepository(BaseRepository[Token]):
    def __init__(self, session: Annotated[AsyncSession, Depends(get_session)]):
        super().__init__(Token, session)
