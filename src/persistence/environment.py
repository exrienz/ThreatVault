from fastapi import Depends
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.domain.entity import Environment
from src.infrastructure.database.session import get_session
from src.persistence.base import BaseRepository


class EnvRepository(BaseRepository[Environment]):
    def __init__(self, session: AsyncSession = Depends(get_session)):
        super().__init__(Environment, session)

    def _options(self, stmt: Select):
        return stmt.options(joinedload(Environment.project)).options(
            joinedload(Environment.products)
        )
